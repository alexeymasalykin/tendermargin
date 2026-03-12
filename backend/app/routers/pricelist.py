from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.pricelist import (
    PricelistMapRequest,
    PricelistMapStarted,
    PricelistMapStatus,
    PricelistMatchBatchUpdate,
    PricelistMatchOut,
    PricelistStructure,
    PricelistUploadResult,
)
from app.services.pricelist_service import (
    detect_structure,
    get_task_status,
    list_pricelist_matches,
    start_mapping_task,
    update_matches,
    upload_pricelist,
)
from app.services.project_service import get_project_or_404

router = APIRouter(tags=["pricelist"])


@router.post(
    "/projects/{project_id}/pricelist/upload",
    response_model=PricelistUploadResult,
)
async def upload_pricelist_file(
    project_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PricelistUploadResult:
    await get_project_or_404(project_id, current_user.id, db)
    return await upload_pricelist(project_id, file, db)


@router.post(
    "/projects/{project_id}/pricelist/detect-structure",
    response_model=PricelistStructure,
)
async def detect_pricelist_structure(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PricelistStructure:
    await get_project_or_404(project_id, current_user.id, db)
    return await detect_structure(project_id, db)


@router.post(
    "/projects/{project_id}/pricelist/map",
    response_model=PricelistMapStarted,
)
async def start_map(
    project_id: uuid.UUID,
    body: PricelistMapRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PricelistMapStarted:
    await get_project_or_404(project_id, current_user.id, db)
    task_id = start_mapping_task(project_id, body.structure, current_user.id, db)
    return PricelistMapStarted(task_id=task_id)


@router.get(
    "/projects/{project_id}/pricelist/map/status",
    response_model=PricelistMapStatus,
)
async def get_map_status(
    project_id: uuid.UUID,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PricelistMapStatus:
    await get_project_or_404(project_id, current_user.id, db)
    return get_task_status(task_id)


@router.get(
    "/projects/{project_id}/pricelist/matches",
    response_model=List[PricelistMatchOut],
)
async def get_pricelist_matches(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PricelistMatchOut]:
    await get_project_or_404(project_id, current_user.id, db)
    return await list_pricelist_matches(project_id, db)


@router.put(
    "/projects/{project_id}/pricelist/matches",
    response_model=List[PricelistMatchOut],
)
async def update_pricelist_matches(
    project_id: uuid.UUID,
    body: PricelistMatchBatchUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PricelistMatchOut]:
    await get_project_or_404(project_id, current_user.id, db)
    return await update_matches(
        project_id,
        [u.model_dump() for u in body.updates],
        current_user.id,
        db,
    )
