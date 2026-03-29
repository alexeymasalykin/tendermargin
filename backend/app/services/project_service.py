from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contractor import ContractorPrice
from app.models.material import Material
from app.models.pricelist import PricelistMatch, PricelistUpload
from app.models.project import Project
from app.models.smeta import SmetaItem, SmetaUpload
from app.schemas.project import (
    ContractorProgress,
    MarginProgress,
    MaterialsProgress,
    PricelistProgress,
    ProjectProgress,
    SmetaProgress,
)


async def get_project_or_404(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Project:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user_id,
            Project.active(),
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def build_progress(project_id: uuid.UUID, db: AsyncSession) -> ProjectProgress:
    # --- Smeta ---
    smeta_upload_result = await db.execute(
        select(SmetaUpload).where(SmetaUpload.project_id == project_id)
    )
    smeta_upload = smeta_upload_result.scalar_one_or_none()

    # Batch: item count + total sum in one query
    counts = await db.execute(
        select(
            func.count(SmetaItem.id).label("item_count"),
            func.coalesce(func.sum(SmetaItem.total_price), 0).label("total_sum"),
        ).where(SmetaItem.project_id == project_id)
    )
    row = counts.one()
    item_count = row.item_count
    total_sum = float(row.total_sum)

    if smeta_upload is None or smeta_upload.parsed_at is None:
        smeta_progress = SmetaProgress(status="not_started")
    else:
        smeta_progress = SmetaProgress(status="completed", item_count=item_count, total_sum=total_sum)

    # --- Materials ---
    mat_count_result = await db.execute(
        select(func.count(Material.id)).where(Material.project_id == project_id)
    )
    total_materials = mat_count_result.scalar_one()

    # --- Contractor (batch: total + filled in one query) ---
    contractor_counts = await db.execute(
        select(
            func.count(ContractorPrice.id).label("total"),
            func.count(ContractorPrice.id).filter(ContractorPrice.price.is_not(None)).label("filled"),
        ).where(ContractorPrice.project_id == project_id)
    )
    c_row = contractor_counts.one()
    total_contractor = c_row.total
    filled_contractor = c_row.filled

    # --- Pricelist (batch: total + accepted in one query) ---
    pricelist_counts = await db.execute(
        select(
            func.count(PricelistMatch.id).label("total"),
            func.count(PricelistMatch.id).filter(PricelistMatch.status == "accepted").label("accepted"),
        ).where(PricelistMatch.project_id == project_id)
    )
    p_row = pricelist_counts.one()

    # Materials progress
    if total_materials == 0:
        materials_progress = MaterialsProgress(status="not_started")
    else:
        filled_materials_result = await db.execute(
            select(func.count(PricelistMatch.id)).where(
                PricelistMatch.project_id == project_id,
                PricelistMatch.supplier_price.is_not(None),
            )
        )
        filled_materials = filled_materials_result.scalar_one()
        mat_status = (
            "completed" if filled_materials == total_materials
            else ("in_progress" if filled_materials > 0 else "not_started")
        )
        materials_progress = MaterialsProgress(status=mat_status, filled=filled_materials, total=total_materials)

    # Contractor progress
    if total_contractor == 0:
        contractor_progress = ContractorProgress(status="not_started")
    else:
        cont_status = (
            "completed" if filled_contractor == total_contractor
            else ("in_progress" if filled_contractor > 0 else "not_started")
        )
        contractor_progress = ContractorProgress(status=cont_status, filled=filled_contractor, total=total_contractor)

    # Pricelist progress
    pricelist_upload_result = await db.execute(
        select(PricelistUpload)
        .where(PricelistUpload.project_id == project_id)
        .order_by(PricelistUpload.created_at.desc())
        .limit(1)
    )
    pricelist_upload = pricelist_upload_result.scalar_one_or_none()

    if pricelist_upload is None:
        pricelist_progress = PricelistProgress(status="not_started")
    else:
        total_matches = p_row.total
        accepted = p_row.accepted
        pl_status = "completed" if total_matches > 0 and accepted == total_matches else "in_progress"
        pricelist_progress = PricelistProgress(status=pl_status)

    # --- Margin ---
    smeta_done = smeta_progress.status == "completed"
    has_any_contractor = filled_contractor > 0

    margin_available = smeta_done and has_any_contractor
    margin_pct: Optional[float] = None

    if margin_available:
        rows = await db.execute(
            select(SmetaItem.total_price, SmetaItem.quantity, ContractorPrice.price)
            .outerjoin(
                ContractorPrice,
                (ContractorPrice.smeta_item_id == SmetaItem.id)
                & (ContractorPrice.project_id == project_id),
            )
            .where(SmetaItem.project_id == project_id)
        )
        total_ceiling = 0.0
        total_cost = 0.0
        for tp, qty, price in rows.all():
            c = float(tp)
            total_ceiling += c
            if price is not None:
                total_cost += float(price) * float(qty)
            else:
                total_cost += c
        if total_ceiling > 0:
            margin_pct = round((total_ceiling - total_cost) / total_ceiling * 100, 2)

    margin_progress = MarginProgress(available=margin_available, margin_pct=margin_pct)

    return ProjectProgress(
        smeta=smeta_progress,
        materials=materials_progress,
        contractor=contractor_progress,
        pricelist=pricelist_progress,
        margin=margin_progress,
    )
