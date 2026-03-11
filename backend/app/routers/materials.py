from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.materials import MaterialOut
from app.services.materials_service import export_materials_excel, list_materials
from app.services.project_service import get_project_or_404

router = APIRouter(tags=["materials"])


@router.get("/projects/{project_id}/materials", response_model=List[MaterialOut])
async def get_materials(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[MaterialOut]:
    await get_project_or_404(project_id, current_user.id, db)
    return await list_materials(project_id, db)


@router.post("/projects/{project_id}/materials/export")
async def export_materials(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await get_project_or_404(project_id, current_user.id, db)
    content = await export_materials_excel(project_id, db)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="materials_{project_id}.xlsx"'
        },
    )
