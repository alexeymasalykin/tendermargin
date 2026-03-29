from __future__ import annotations

import math
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.smeta import SmetaItem
from app.models.user import User
from app.schemas.smeta import SmetaItemOut, SmetaItemsPage, SmetaUploadResult
from app.services.project_service import get_project_or_404
from app.services.smeta_service import process_smeta_upload

router = APIRouter(tags=["smeta"])

SORT_COLUMNS = {
    "number": SmetaItem.number,
    "name": SmetaItem.name,
    "total_price": SmetaItem.total_price,
    "item_type": SmetaItem.item_type,
}


@router.post("/projects/{project_id}/smeta/upload", response_model=SmetaUploadResult)
async def upload_smeta(
    project_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SmetaUploadResult:
    await get_project_or_404(project_id, current_user.id, db)
    result = await process_smeta_upload(project_id, current_user.id, file, db)
    return SmetaUploadResult(**result)


@router.get("/projects/{project_id}/smeta/items", response_model=SmetaItemsPage)
async def get_smeta_items(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort: Optional[str] = Query(None, pattern="^(number|name|total_price|item_type)$"),
    filter_type: Optional[str] = Query(None, alias="filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SmetaItemsPage:
    await get_project_or_404(project_id, current_user.id, db)

    base_query = select(SmetaItem).where(SmetaItem.project_id == project_id)
    if filter_type:
        base_query = base_query.where(SmetaItem.item_type == filter_type)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    sort_col = SORT_COLUMNS.get(sort or "number", SmetaItem.number)
    query = (
        base_query.order_by(sort_col)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return SmetaItemsPage(
        items=[SmetaItemOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )
