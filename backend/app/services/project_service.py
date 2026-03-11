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
    ProjectDetail,
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
            Project.deleted_at.is_(None),
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

    if smeta_upload is None or smeta_upload.parsed_at is None:
        smeta_progress = SmetaProgress(status="not_started")
    else:
        item_count_result = await db.execute(
            select(func.count(SmetaItem.id)).where(SmetaItem.project_id == project_id)
        )
        item_count = item_count_result.scalar_one()

        total_sum_result = await db.execute(
            select(func.coalesce(func.sum(SmetaItem.total_price), 0)).where(
                SmetaItem.project_id == project_id
            )
        )
        total_sum = float(total_sum_result.scalar_one())
        smeta_progress = SmetaProgress(
            status="completed", item_count=item_count, total_sum=total_sum
        )

    # --- Materials ---
    total_materials_result = await db.execute(
        select(func.count(Material.id)).where(Material.project_id == project_id)
    )
    total_materials = total_materials_result.scalar_one()

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
            "completed"
            if filled_materials == total_materials
            else ("in_progress" if filled_materials > 0 else "not_started")
        )
        materials_progress = MaterialsProgress(
            status=mat_status,
            filled=filled_materials,
            total=total_materials,
        )

    # --- Contractor ---
    total_contractor_result = await db.execute(
        select(func.count(ContractorPrice.id)).where(
            ContractorPrice.project_id == project_id
        )
    )
    total_contractor = total_contractor_result.scalar_one()

    if total_contractor == 0:
        contractor_progress = ContractorProgress(status="not_started")
    else:
        filled_contractor_result = await db.execute(
            select(func.count(ContractorPrice.id)).where(
                ContractorPrice.project_id == project_id,
                ContractorPrice.price.is_not(None),
            )
        )
        filled_contractor = filled_contractor_result.scalar_one()
        cont_status = (
            "completed"
            if filled_contractor == total_contractor
            else ("in_progress" if filled_contractor > 0 else "not_started")
        )
        contractor_progress = ContractorProgress(
            status=cont_status,
            filled=filled_contractor,
            total=total_contractor,
        )

    # --- Pricelist ---
    pricelist_result = await db.execute(
        select(PricelistUpload).where(PricelistUpload.project_id == project_id)
    )
    pricelist_upload = pricelist_result.scalar_one_or_none()

    if pricelist_upload is None:
        pricelist_progress = PricelistProgress(status="not_started")
    else:
        total_matches_result = await db.execute(
            select(func.count(PricelistMatch.id)).where(
                PricelistMatch.project_id == project_id
            )
        )
        total_matches = total_matches_result.scalar_one()
        accepted_result = await db.execute(
            select(func.count(PricelistMatch.id)).where(
                PricelistMatch.project_id == project_id,
                PricelistMatch.status == "accepted",
            )
        )
        accepted = accepted_result.scalar_one()
        pl_status = (
            "completed"
            if total_matches > 0 and accepted == total_matches
            else "in_progress"
        )
        pricelist_progress = PricelistProgress(status=pl_status)

    # --- Margin ---
    smeta_done = smeta_progress.status == "completed"
    has_any_contractor = contractor_progress.filled > 0

    margin_available = smeta_done and has_any_contractor
    margin_pct: Optional[float] = None

    if margin_available:
        ceiling_result = await db.execute(
            select(func.coalesce(func.sum(SmetaItem.total_price), 0)).where(
                SmetaItem.project_id == project_id
            )
        )
        total_ceiling = float(ceiling_result.scalar_one())

        cost_result = await db.execute(
            select(
                func.coalesce(
                    func.sum(SmetaItem.quantity * ContractorPrice.price), 0
                )
            ).select_from(ContractorPrice)
            .join(SmetaItem, ContractorPrice.smeta_item_id == SmetaItem.id)
            .where(
                ContractorPrice.project_id == project_id,
                ContractorPrice.price.is_not(None),
            )
        )
        total_cost = float(cost_result.scalar_one())

        if total_ceiling > 0 and total_cost > 0:
            margin_pct = round((total_ceiling - total_cost) / total_ceiling * 100, 2)

    margin_progress = MarginProgress(available=margin_available, margin_pct=margin_pct)

    return ProjectProgress(
        smeta=smeta_progress,
        materials=materials_progress,
        contractor=contractor_progress,
        pricelist=pricelist_progress,
        margin=margin_progress,
    )
