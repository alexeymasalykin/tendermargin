from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.margin import MarginResult
from app.services.margin_service import calculate_margin, export_margin_excel
from app.services.project_service import get_project_or_404

router = APIRouter(tags=["margin"])


@router.get("/projects/{project_id}/margin", response_model=MarginResult)
async def get_margin(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MarginResult:
    await get_project_or_404(project_id, current_user.id, db)
    return await calculate_margin(project_id, db)


@router.post("/projects/{project_id}/margin/export")
async def export_margin(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await get_project_or_404(project_id, current_user.id, db)
    content = await export_margin_excel(project_id, db)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="margin_{project_id}.xlsx"'
        },
    )
