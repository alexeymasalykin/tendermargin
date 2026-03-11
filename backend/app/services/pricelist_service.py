from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.material import Material
from app.models.pricelist import PricelistMatch, PricelistUpload
from app.schemas.pricelist import (
    PricelistMatchOut,
    PricelistMatchPartial,
    PricelistMapStatus,
    PricelistStructure,
    PricelistUploadResult,
)

# In-memory task registry: { task_id: PricelistMapStatus }
_TASK_REGISTRY: Dict[str, PricelistMapStatus] = {}

ALLOWED_PRICELIST_EXTENSIONS = {".xlsx", ".xls"}


def _validate_pricelist_file(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_PRICELIST_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid extension '{ext}'. Allowed: .xlsx, .xls",
        )


async def upload_pricelist(
    project_id: uuid.UUID,
    upload: UploadFile,
    db: AsyncSession,
) -> PricelistUploadResult:
    _validate_pricelist_file(upload.filename or "")
    content = await upload.read()

    upload_dir = Path(settings.upload_dir) / str(project_id) / "pricelist"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / (upload.filename or "pricelist.xlsx")
    file_path.write_bytes(content)

    pl_upload = PricelistUpload(
        project_id=project_id,
        filename=upload.filename or "pricelist.xlsx",
        file_path=str(file_path),
    )
    db.add(pl_upload)
    await db.commit()
    await db.refresh(pl_upload)

    return PricelistUploadResult(upload_id=pl_upload.id, filename=pl_upload.filename)


async def detect_structure(
    project_id: uuid.UUID, db: AsyncSession
) -> PricelistStructure:
    result = await db.execute(
        select(PricelistUpload)
        .where(PricelistUpload.project_id == project_id)
        .order_by(PricelistUpload.created_at.desc())
        .limit(1)
    )
    pl_upload = result.scalar_one_or_none()
    if pl_upload is None:
        raise HTTPException(status_code=400, detail="No pricelist uploaded for this project")

    try:
        from core.pricelist_mapper import detect_structure as core_detect
        structure_data = core_detect(pl_upload.file_path)
        if not isinstance(structure_data, dict):
            structure_data = vars(structure_data)
    except (ImportError, Exception):
        structure_data = {}

    pl_upload.structure_json = structure_data
    await db.commit()

    return PricelistStructure(
        name_column=structure_data.get("name_column"),
        unit_column=structure_data.get("unit_column"),
        price_column=structure_data.get("price_column"),
        raw_columns=structure_data.get("raw_columns", []),
        extra={k: v for k, v in structure_data.items()
               if k not in {"name_column", "unit_column", "price_column", "raw_columns"}},
    )


async def _run_mapping_task(
    task_id: str,
    project_id: uuid.UUID,
    structure: PricelistStructure,
    db: AsyncSession,
) -> None:
    task = _TASK_REGISTRY[task_id]
    try:
        mat_result = await db.execute(
            select(Material).where(Material.project_id == project_id)
        )
        materials = mat_result.scalars().all()

        pl_result = await db.execute(
            select(PricelistUpload)
            .where(PricelistUpload.project_id == project_id)
            .order_by(PricelistUpload.created_at.desc())
            .limit(1)
        )
        pl_upload = pl_result.scalar_one_or_none()
        if pl_upload is None:
            raise ValueError("No pricelist upload found")

        task.total = len(materials)

        try:
            from core.pricelist_mapper import map_materials
            loop = asyncio.get_event_loop()
            matches_raw = await loop.run_in_executor(
                None,
                map_materials,
                pl_upload.file_path,
                [m.name for m in materials],
                {
                    "name_column": structure.name_column,
                    "unit_column": structure.unit_column,
                    "price_column": structure.price_column,
                },
            )
        except ImportError:
            matches_raw = [{"supplier_name": None, "supplier_price": None, "confidence": 0.0}
                           for _ in materials]

        await db.execute(
            delete(PricelistMatch).where(PricelistMatch.project_id == project_id)
        )

        for i, (mat, match) in enumerate(zip(materials, matches_raw)):
            confidence = float(match.get("confidence", 0))
            status = "accepted" if confidence >= 0.85 else "pending"
            pm = PricelistMatch(
                project_id=project_id,
                material_id=mat.id,
                supplier_name=match.get("supplier_name"),
                supplier_price=match.get("supplier_price"),
                confidence=confidence,
                status=status,
            )
            db.add(pm)

            partial = PricelistMatchPartial(
                material_name=mat.name,
                supplier_name=match.get("supplier_name"),
                supplier_price=match.get("supplier_price"),
                confidence=confidence,
                status=status,
            )
            task.matches.append(partial)
            task.progress = i + 1

            if (i + 1) % 5 == 0:
                await db.flush()
                await asyncio.sleep(0)

        await db.commit()
        task.status = "completed"

    except Exception as exc:
        task.status = "failed"
        task.error = str(exc)
        try:
            await db.rollback()
        except Exception:
            pass


def start_mapping_task(
    project_id: uuid.UUID,
    structure: PricelistStructure,
    db: AsyncSession,
) -> str:
    task_id = str(uuid.uuid4())
    _TASK_REGISTRY[task_id] = PricelistMapStatus(
        status="running", progress=0, total=0, matches=[]
    )
    asyncio.ensure_future(
        _run_mapping_task(task_id, project_id, structure, db)
    )
    return task_id


def get_task_status(task_id: str) -> PricelistMapStatus:
    task = _TASK_REGISTRY.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


async def list_pricelist_matches(
    project_id: uuid.UUID, db: AsyncSession
) -> List[PricelistMatchOut]:
    result = await db.execute(
        select(PricelistMatch)
        .where(PricelistMatch.project_id == project_id)
        .order_by(PricelistMatch.updated_at)
    )
    matches = result.scalars().all()
    return [PricelistMatchOut.model_validate(m) for m in matches]


async def update_matches(
    project_id: uuid.UUID,
    updates: List[dict],
    db: AsyncSession,
) -> List[PricelistMatchOut]:
    result = await db.execute(
        select(PricelistMatch).where(PricelistMatch.project_id == project_id)
    )
    matches_map = {str(m.id): m for m in result.scalars().all()}

    updated = []
    for upd in updates:
        match = matches_map.get(str(upd["id"]))
        if match is None:
            raise HTTPException(
                status_code=404, detail=f"Match {upd['id']} not found"
            )
        if upd.get("supplier_price") is not None:
            match.supplier_price = upd["supplier_price"]
        if upd.get("status") is not None:
            match.status = upd["status"]
        match.updated_at = datetime.now(timezone.utc)
        updated.append(match)

    await db.commit()
    return [PricelistMatchOut.model_validate(m) for m in updated]
