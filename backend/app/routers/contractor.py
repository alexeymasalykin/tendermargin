from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.contractor import (
    ContractorPriceBatchUpdate,
    ContractorPriceOut,
    ContractorPriceSingleUpdate,
)
from app.services.contractor_service import (
    list_contractor_prices,
    update_contractor_price,
)
from app.services.project_service import get_project_or_404

router = APIRouter(tags=["contractor"])


@router.get(
    "/projects/{project_id}/contractor-prices",
    response_model=List[ContractorPriceOut],
)
async def get_contractor_prices(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ContractorPriceOut]:
    await get_project_or_404(project_id, current_user.id, db)
    return await list_contractor_prices(project_id, db)


@router.put(
    "/projects/{project_id}/contractor-prices",
    response_model=List[ContractorPriceOut],
)
async def batch_update_contractor_prices(
    project_id: uuid.UUID,
    body: ContractorPriceBatchUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ContractorPriceOut]:
    await get_project_or_404(project_id, current_user.id, db)
    results = []
    for update in body.prices:
        result = await update_contractor_price(
            project_id, update.smeta_item_id, update.price, current_user.id, db
        )
        results.append(result)
    return results


@router.put(
    "/projects/{project_id}/contractor-prices/{smeta_item_id}",
    response_model=ContractorPriceOut,
)
async def update_single_contractor_price(
    project_id: uuid.UUID,
    smeta_item_id: uuid.UUID,
    body: ContractorPriceSingleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContractorPriceOut:
    await get_project_or_404(project_id, current_user.id, db)
    return await update_contractor_price(
        project_id, smeta_item_id, body.price, current_user.id, db
    )
