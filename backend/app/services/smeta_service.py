from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

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
    content = await upload.read()
    _validate_file(upload.filename or "", content)

    await _cascade_delete_smeta(project_id, db)

    upload_dir = Path(settings.upload_dir) / str(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / (upload.filename or "smeta")
    file_path.write_bytes(content)

    smeta_upload = SmetaUpload(
        project_id=project_id,
        filename=upload.filename or "smeta",
        file_path=str(file_path),
    )
    db.add(smeta_upload)
    await db.flush()

    ext = Path(upload.filename or "").suffix.lower()
    if ext == ".pdf":
        parse_result = parse_pdf(str(file_path))
    else:
        parse_result = parse_excel(str(file_path))

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
    return {
        "item_count": len(items_to_add),
        "total_sum": sum(float(i.total_price) for i in items_to_add),
    }
