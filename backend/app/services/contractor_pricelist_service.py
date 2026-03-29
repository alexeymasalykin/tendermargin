"""Contractor work pricelist upload, structure detection, and AI mapping to smeta items."""
from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.contractor import ContractorPrice, ContractorPriceLibrary
from app.models.smeta import SmetaItem
from app.schemas.pricelist import (
    PricelistMapStatus,
    PricelistMatchPartial,
    PricelistStructure,
    PricelistUploadResult,
)

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".pdf"}

# In-memory task registry for contractor mapping
_TASK_REGISTRY: Dict[str, PricelistMapStatus] = {}
_TASK_CREATED: Dict[str, datetime] = {}
_TASK_TTL_SECONDS = 3600  # 1 hour


def _cleanup_stale_tasks() -> None:
    """Remove completed/failed tasks older than TTL."""
    now = datetime.now(timezone.utc)
    stale = [
        tid for tid, created in _TASK_CREATED.items()
        if (now - created).total_seconds() > _TASK_TTL_SECONDS
        and _TASK_REGISTRY.get(tid, PricelistMapStatus(status="completed", progress=0, total=0, matches=[])).status in ("completed", "failed")
    ]
    for tid in stale:
        _TASK_REGISTRY.pop(tid, None)
        _TASK_CREATED.pop(tid, None)


def _validate_file(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid extension '{ext}'. Allowed: .xlsx, .xls, .pdf",
        )


async def upload_contractor_pricelist(
    project_id: uuid.UUID,
    upload: UploadFile,
    db: AsyncSession,
) -> PricelistUploadResult:
    _validate_file(upload.filename or "")
    content = await upload.read()

    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
        )

    upload_dir = Path(settings.upload_dir) / str(project_id) / "contractor_pricelist"
    # Clean old files before new upload
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(upload.filename or "contractor_pricelist.xlsx").name
    file_path = upload_dir / filename
    file_path.write_bytes(content)

    upload_id = uuid.uuid4()
    return PricelistUploadResult(upload_id=upload_id, filename=filename)


async def detect_contractor_structure(
    project_id: uuid.UUID,
) -> PricelistStructure:
    upload_dir = Path(settings.upload_dir) / str(project_id) / "contractor_pricelist"
    files = sorted(upload_dir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True) if upload_dir.exists() else []
    if not files:
        raise HTTPException(status_code=400, detail="No contractor pricelist uploaded")

    file_path = str(files[0])

    try:
        from core.pricelist_mapper import detect_structure as core_detect

        loop = asyncio.get_running_loop()
        structure_data = await loop.run_in_executor(None, core_detect, file_path)
        if not isinstance(structure_data, dict):
            structure_data = vars(structure_data)
    except Exception as exc:
        logger.exception("Structure detection failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Structure detection failed: {exc}")

    return PricelistStructure(
        name_column=structure_data.get("name_column"),
        unit_column=structure_data.get("unit_column"),
        price_column=structure_data.get("price_column"),
        raw_columns=structure_data.get("raw_columns", []),
        extra={k: v for k, v in structure_data.items()
               if k not in {"name_column", "unit_column", "price_column", "raw_columns"}},
    )


async def _run_contractor_mapping_task(
    task_id: str,
    project_id: uuid.UUID,
    structure: PricelistStructure,
    user_id: uuid.UUID,
) -> None:
    from app.database import AsyncSessionLocal

    task = _TASK_REGISTRY[task_id]
    async with AsyncSessionLocal() as db:
        try:
            # Get smeta items (work positions)
            si_result = await db.execute(
                select(SmetaItem)
                .where(SmetaItem.project_id == project_id)
                .order_by(SmetaItem.number)
            )
            smeta_items = si_result.scalars().all()
            task.total = len(smeta_items)

            if not smeta_items:
                task.status = "failed"
                task.error = "No smeta items found. Upload a smeta first."
                return

            # Find the uploaded file
            upload_dir = Path(settings.upload_dir) / str(project_id) / "contractor_pricelist"
            files = sorted(upload_dir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True) if upload_dir.exists() else []
            if not files:
                task.status = "failed"
                task.error = "Contractor pricelist file not found"
                return
            file_path = str(files[0])

            # Library lookup: check cached prices first
            lib_result = await db.execute(
                select(ContractorPriceLibrary).where(ContractorPriceLibrary.user_id == user_id)
            )
            library = {e.fsnb_code: e for e in lib_result.scalars().all()}

            cached: dict[int, dict] = {}
            items_for_llm: list[tuple[int, SmetaItem]] = []

            for i, si in enumerate(smeta_items):
                lib_entry = library.get(si.code) if si.code else None
                if lib_entry and lib_entry.price is not None:
                    cached[i] = {
                        "supplier_name": lib_entry.name,
                        "supplier_price": float(lib_entry.price),
                        "confidence": 1.0,
                    }
                else:
                    items_for_llm.append((i, si))

            try:
                from core.pricelist_mapper import (
                    PricelistStructure as CoreStructure,
                    WorkItem,
                    map_works,
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

                loop = asyncio.get_running_loop()
                pricelist_items = await loop.run_in_executor(
                    None, read_pricelist_data, file_path, core_structure,
                )

                work_rows = [
                    WorkItem(
                        index=orig_idx,
                        name=si.name,
                        unit=si.unit or "",
                        quantity=float(si.quantity),
                        ceiling_price=float(si.total_price),
                        code=si.code or "",
                    )
                    for orig_idx, si in items_for_llm
                ]

                if work_rows and pricelist_items:
                    matches_raw = await loop.run_in_executor(
                        None, map_works, work_rows, pricelist_items,
                    )
                else:
                    matches_raw = []

                best_by_item: dict[int, dict] = {}
                for mm in matches_raw:
                    idx = mm.material_index
                    entry = {
                        "supplier_name": mm.supplier_name,
                        "supplier_price": mm.supplier_price,
                        "confidence": mm.confidence,
                    }
                    if idx not in best_by_item or mm.confidence > best_by_item[idx]["confidence"]:
                        best_by_item[idx] = entry

                best_by_item.update(cached)

                matches_dicts = [
                    best_by_item.get(i, {"supplier_name": None, "supplier_price": None, "confidence": 0.0})
                    for i in range(len(smeta_items))
                ]
            except ImportError as imp_err:
                logger.error("core.pricelist_mapper import failed: %s", imp_err)
                task.status = "failed"
                task.error = f"Модуль маппинга не найден: {imp_err}"
                return

            # Update ContractorPrice records with matched/cached prices
            for i, (si, match) in enumerate(zip(smeta_items, matches_dicts)):
                confidence = min(1.0, max(0.0, float(match.get("confidence", 0))))
                price = match.get("supplier_price")

                if price is not None and confidence >= 0.5:
                    # Find existing contractor price for this smeta item
                    cp_result = await db.execute(
                        select(ContractorPrice).where(
                            ContractorPrice.project_id == project_id,
                            ContractorPrice.smeta_item_id == si.id,
                        )
                    )
                    cp = cp_result.scalar_one_or_none()
                    if cp:
                        cp.price = price
                        cp.updated_at = datetime.now(timezone.utc)

                        # Sync to library
                        if cp.fsnb_code:
                            lib_entry = library.get(cp.fsnb_code)
                            if lib_entry:
                                lib_entry.price = price
                                lib_entry.updated_at = datetime.now(timezone.utc)
                            else:
                                new_lib = ContractorPriceLibrary(
                                    user_id=user_id,
                                    fsnb_code=cp.fsnb_code,
                                    name=si.name,
                                    unit=si.unit or "",
                                    price=price,
                                )
                                db.add(new_lib)

                status = "accepted" if confidence >= 0.85 else "pending"
                partial = PricelistMatchPartial(
                    material_name=si.name,
                    supplier_name=match.get("supplier_name"),
                    supplier_price=price,
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
            logger.exception("Contractor mapping failed: %s", exc)
            task.status = "failed"
            task.error = str(exc)
            try:
                await db.rollback()
            except Exception:
                logger.warning("Rollback failed after mapping error")


def start_contractor_mapping_task(
    project_id: uuid.UUID,
    structure: PricelistStructure,
    user_id: uuid.UUID,
) -> str:
    _cleanup_stale_tasks()
    task_id = str(uuid.uuid4())
    _TASK_REGISTRY[task_id] = PricelistMapStatus(
        status="running", progress=0, total=0, matches=[]
    )
    _TASK_CREATED[task_id] = datetime.now(timezone.utc)
    asyncio.ensure_future(
        _run_contractor_mapping_task(task_id, project_id, structure, user_id)
    )
    return task_id


def get_contractor_task_status(task_id: str) -> PricelistMapStatus:
    task = _TASK_REGISTRY.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
