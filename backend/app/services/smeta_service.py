from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.contractor import ContractorPrice, ContractorPriceLibrary
from app.models.material import Material
from app.models.pricelist import PricelistMatch, PricelistUpload
from app.models.smeta import SmetaItem, SmetaUpload

try:
    from core.parser_excel import parse_excel
    from core.parser_pdf import parse_pdf
    from core.materials import aggregate_materials, _normalize_unit
except ImportError:
    parse_excel = None  # type: ignore
    parse_pdf = None  # type: ignore
    aggregate_materials = None  # type: ignore
    _normalize_unit = None  # type: ignore

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".pdf"}
MAGIC_SIGNATURES = {
    b"\x50\x4b\x03\x04": "xlsx/xls zip-based",
    b"\xd0\xcf\x11\xe0": "xls legacy",
    b"\x25\x50\x44\x46": "pdf",
}


def _validate_file(filename: str, content: bytes) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    if not any(content.startswith(sig) for sig in MAGIC_SIGNATURES):
        raise HTTPException(
            status_code=400,
            detail="File content does not match a valid Excel or PDF format (magic bytes check failed)",
        )


async def _cascade_delete_smeta(project_id: uuid.UUID, db: AsyncSession) -> None:
    await db.execute(delete(PricelistMatch).where(PricelistMatch.project_id == project_id))
    await db.execute(delete(PricelistUpload).where(PricelistUpload.project_id == project_id))
    await db.execute(delete(ContractorPrice).where(ContractorPrice.project_id == project_id))
    await db.execute(delete(Material).where(Material.project_id == project_id))
    await db.execute(delete(SmetaItem).where(SmetaItem.project_id == project_id))
    await db.execute(delete(SmetaUpload).where(SmetaUpload.project_id == project_id))


async def process_smeta_upload(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    upload: UploadFile,
    db: AsyncSession,
) -> dict:
    """Upload and save file, return upload_id. Parsing happens in background."""
    content = await upload.read()

    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
        )

    _validate_file(upload.filename or "", content)

    await _cascade_delete_smeta(project_id, db)

    upload_dir = Path(settings.upload_dir) / str(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(upload.filename).name if upload.filename else "smeta"
    file_path = upload_dir / safe_filename
    file_path.write_bytes(content)

    smeta_upload = SmetaUpload(
        project_id=project_id,
        filename=safe_filename,
        file_path=str(file_path),
    )
    db.add(smeta_upload)
    await db.commit()
    await db.refresh(smeta_upload)

    return {
        "upload_id": str(smeta_upload.id),
        "filename": safe_filename,
    }


async def parse_smeta_background(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    upload_id: uuid.UUID,
    file_path: str,
) -> None:
    """Parse uploaded smeta file in background. Creates its own DB session."""
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(SmetaUpload).where(SmetaUpload.id == upload_id)
            )
            smeta_upload = result.scalar_one_or_none()
            if smeta_upload is None:
                logger.error("SmetaUpload %s not found for background parse", upload_id)
                return

            ext = Path(file_path).suffix.lower()
            if ext == ".pdf":
                parse_result = parse_pdf(file_path)
            else:
                parse_result = parse_excel(file_path)

            items_to_add = []
            for item in parse_result.items:
                raw_unit = item.unit or ""
                raw_qty = float(item.quantity or 0)
                norm_unit, norm_qty = _normalize_unit(raw_unit, raw_qty)
                smeta_item = SmetaItem(
                    project_id=project_id,
                    number=item.number,
                    code=item.code or "",
                    name=item.name,
                    unit=norm_unit,
                    quantity=norm_qty,
                    unit_price=float(item.total_price / norm_qty) if norm_qty else 0,
                    total_price=float(item.total_price or 0),
                    item_type=item.item_type or "unknown",
                    section=item.section or "",
                )
                items_to_add.append(smeta_item)

            db.add_all(items_to_add)
            await db.flush()

            smeta_upload.parsed_at = datetime.now(timezone.utc)

            material_rows = aggregate_materials(parse_result.items)
            materials_to_add = []
            for mat in material_rows:
                material = Material(
                    project_id=project_id,
                    name=mat.name,
                    unit=mat.unit or "",
                    quantity=float(mat.quantity or 0),
                    smeta_total=float(mat.smeta_total or 0),
                    codes=mat.codes or [],
                )
                materials_to_add.append(material)
            db.add_all(materials_to_add)

            work_items = [i for i in items_to_add if i.item_type == "work"]
            if work_items:
                fsnb_codes = [i.code for i in work_items if i.code]
                library_result = await db.execute(
                    select(ContractorPriceLibrary).where(
                        ContractorPriceLibrary.user_id == user_id,
                        ContractorPriceLibrary.fsnb_code.in_(fsnb_codes),
                    )
                )
                library_map: dict[str, ContractorPriceLibrary] = {
                    lib.fsnb_code: lib for lib in library_result.scalars().all()
                }
                contractor_prices = []
                for item in work_items:
                    lib_entry = library_map.get(item.code or "")
                    contractor_prices.append(
                        ContractorPrice(
                            project_id=project_id,
                            smeta_item_id=item.id,
                            fsnb_code=item.code or "",
                            name=item.name,
                            unit=item.unit or "",
                            price=lib_entry.price if lib_entry else None,
                        )
                    )
                db.add_all(contractor_prices)

            await db.commit()
            logger.info("Parsed smeta %s: %d items", upload_id, len(items_to_add))

        except Exception as e:
            logger.error("Background smeta parse failed for %s: %s", upload_id, e, exc_info=True)
            await db.rollback()
