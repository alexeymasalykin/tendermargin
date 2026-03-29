from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

import logging

from app.config import settings
from app.models.material import Material
from app.models.pricelist import PricelistMatch, PricelistUpload, SupplierPriceLibrary
from app.schemas.pricelist import (
    PricelistMatchOut,
    PricelistMatchPartial,
    PricelistMapStatus,
    PricelistStructure,
    PricelistUploadResult,
)

logger = logging.getLogger(__name__)

# In-memory task registry: { task_id: PricelistMapStatus }
_TASK_REGISTRY: Dict[str, PricelistMapStatus] = {}

ALLOWED_PRICELIST_EXTENSIONS = {".xlsx", ".xls", ".pdf"}


def _validate_pricelist_file(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_PRICELIST_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid extension '{ext}'. Allowed: .xlsx, .xls, .pdf",
        )


async def upload_pricelist(
    project_id: uuid.UUID,
    upload: UploadFile,
    db: AsyncSession,
) -> PricelistUploadResult:
    _validate_pricelist_file(upload.filename or "")
    content = await upload.read()

    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
        )

    # Clean up previous pricelist data for this project
    await db.execute(delete(PricelistMatch).where(PricelistMatch.project_id == project_id))
    await db.execute(delete(PricelistUpload).where(PricelistUpload.project_id == project_id))

    upload_dir = Path(settings.upload_dir) / str(project_id) / "pricelist"
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(upload.filename or "pricelist.xlsx").name
    file_path = upload_dir / safe_name
    file_path.write_bytes(content)

    pl_upload = PricelistUpload(
        project_id=project_id,
        filename=safe_name,
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
    except ImportError:
        logger.warning("core.pricelist_mapper not available, skipping structure detection")
        structure_data = {}
    except Exception as e:
        logger.error("Failed to detect pricelist structure: %s", e, exc_info=True)
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
    user_id: uuid.UUID,
) -> None:
    from app.database import AsyncSessionLocal

    task = _TASK_REGISTRY[task_id]
    async with AsyncSessionLocal() as db:
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

            # Library lookup: find cached prices for materials (skip LLM for known prices)
            lib_result = await db.execute(
                select(SupplierPriceLibrary).where(SupplierPriceLibrary.user_id == user_id)
            )
            library = {(e.normalized_name, e.unit): e for e in lib_result.scalars().all()}

            # Split materials: cached vs need-LLM
            cached_matches: dict[int, dict] = {}
            materials_for_llm: list[tuple[int, object]] = []
            for i, mat in enumerate(materials):
                norm = _normalize_material_name(mat.name)
                lib_entry = library.get((norm, mat.unit or ""))
                if lib_entry:
                    cached_matches[i] = {
                        "supplier_name": lib_entry.supplier_name,
                        "supplier_price": float(lib_entry.price),
                        "confidence": 1.0,
                    }
                else:
                    materials_for_llm.append((i, mat))

            try:
                from core.materials import MaterialRow
                from core.pricelist_mapper import (
                    PricelistStructure as CoreStructure,
                    map_materials,
                    read_pricelist_data,
                )

                ex = structure.extra or {}
                core_structure = CoreStructure(
                    header_row=int(ex.get("header_row") or 0),
                    name_col=int(ex.get("name_col") or 0),
                    price_col=int(ex.get("price_col") or 0),
                    unit_col=int(ex["unit_col"]) if ex.get("unit_col") is not None else None,
                    vat_included=bool(ex.get("vat_included", True)),
                    vat_rate=float(ex.get("vat_rate") or 20),
                )

                loop = asyncio.get_event_loop()
                pricelist_items = await loop.run_in_executor(
                    None, read_pricelist_data, pl_upload.file_path, core_structure,
                )

                material_rows = [
                    MaterialRow(
                        index=orig_idx,
                        name=m.name,
                        unit=m.unit or "",
                        quantity=float(m.quantity),
                        smeta_total=float(m.smeta_total),
                        codes=m.codes or [],
                    )
                    for orig_idx, m in materials_for_llm
                ]

                if material_rows and pricelist_items:
                    matches_raw = await loop.run_in_executor(
                        None, map_materials, material_rows, pricelist_items,
                    )
                else:
                    matches_raw = []

                best_by_material: dict[int, dict] = {}
                for mm in matches_raw:
                    idx = mm.material_index
                    entry = {
                        "supplier_name": mm.supplier_name,
                        "supplier_price": mm.supplier_price,
                        "confidence": mm.confidence,
                    }
                    if idx not in best_by_material or mm.confidence > best_by_material[idx]["confidence"]:
                        best_by_material[idx] = entry

                best_by_material.update(cached_matches)

                matches_dicts = [
                    best_by_material.get(i, {"supplier_name": None, "supplier_price": None, "confidence": 0.0})
                    for i in range(len(materials))
                ]
            except ImportError:
                matches_dicts = [{"supplier_name": None, "supplier_price": None, "confidence": 0.0}
                                 for _ in materials]

            await db.execute(
                delete(PricelistMatch).where(PricelistMatch.project_id == project_id)
            )

            for i, (mat, match) in enumerate(zip(materials, matches_dicts)):
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
            import logging
            logging.getLogger(__name__).exception("Mapping task failed: %s", exc)
            task.status = "failed"
            task.error = str(exc)
            try:
                await db.rollback()
            except Exception:
                pass


def start_mapping_task(
    project_id: uuid.UUID,
    structure: PricelistStructure,
    user_id: uuid.UUID,
) -> str:
    task_id = str(uuid.uuid4())
    _TASK_REGISTRY[task_id] = PricelistMapStatus(
        status="running", progress=0, total=0, matches=[]
    )
    asyncio.ensure_future(
        _run_mapping_task(task_id, project_id, structure, user_id)
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
        select(PricelistMatch, Material.name)
        .join(Material, PricelistMatch.material_id == Material.id)
        .where(PricelistMatch.project_id == project_id)
        .order_by(PricelistMatch.updated_at)
    )
    return [
        PricelistMatchOut(
            id=m.id,
            material_id=m.material_id,
            material_name=name,
            supplier_name=m.supplier_name,
            supplier_price=float(m.supplier_price) if m.supplier_price is not None else None,
            confidence=float(m.confidence) if m.confidence is not None else None,
            status=m.status,
            updated_at=m.updated_at,
        )
        for m, name in result.all()
    ]


def _normalize_material_name(name: str) -> str:
    """Normalize material name for library lookup: lowercase, collapse whitespace."""
    import re
    s = name.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


async def update_matches(
    project_id: uuid.UUID,
    updates: List[dict],
    user_id: uuid.UUID,
    db: AsyncSession,
) -> List[PricelistMatchOut]:
    result = await db.execute(
        select(PricelistMatch).where(PricelistMatch.project_id == project_id)
    )
    matches_map = {str(m.id): m for m in result.scalars().all()}

    # Pre-load materials for library sync
    mat_result = await db.execute(
        select(Material).where(Material.project_id == project_id)
    )
    materials_by_id = {m.id: m for m in mat_result.scalars().all()}

    updated = []
    library_entries: list[tuple[str, str, str, float]] = []  # (norm_name, supplier_name, unit, price)

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

        # Collect accepted matches for library sync
        if match.status == "accepted" and match.supplier_price is not None:
            mat = materials_by_id.get(match.material_id)
            if mat:
                library_entries.append((
                    _normalize_material_name(mat.name),
                    match.supplier_name or "",
                    mat.unit or "",
                    float(match.supplier_price),
                ))

    # Upsert accepted prices into user's supplier library
    for norm_name, supplier_name, unit, price in library_entries:
        existing = await db.execute(
            select(SupplierPriceLibrary).where(
                SupplierPriceLibrary.user_id == user_id,
                SupplierPriceLibrary.normalized_name == norm_name,
                SupplierPriceLibrary.unit == unit,
            )
        )
        lib_entry = existing.scalar_one_or_none()
        if lib_entry:
            lib_entry.supplier_name = supplier_name
            lib_entry.price = price
            lib_entry.updated_at = datetime.now(timezone.utc)
        else:
            db.add(SupplierPriceLibrary(
                user_id=user_id,
                normalized_name=norm_name,
                supplier_name=supplier_name,
                unit=unit,
                price=price,
                source=f"pricelist",
            ))

    await db.commit()
    return [PricelistMatchOut.model_validate(m) for m in updated]
