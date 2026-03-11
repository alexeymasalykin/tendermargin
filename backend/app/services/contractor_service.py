from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contractor import ContractorPrice, ContractorPriceLibrary
from app.models.smeta import SmetaItem
from app.schemas.contractor import ContractorPriceOut


async def list_contractor_prices(
    project_id: uuid.UUID, db: AsyncSession
) -> List[ContractorPriceOut]:
    result = await db.execute(
        select(ContractorPrice, SmetaItem)
        .join(SmetaItem, ContractorPrice.smeta_item_id == SmetaItem.id)
        .where(ContractorPrice.project_id == project_id)
        .order_by(SmetaItem.number)
    )
    rows = result.all()

    prices = []
    for cp, si in rows:
        total = float(cp.price * si.quantity) if cp.price is not None else None
        prices.append(
            ContractorPriceOut(
                id=cp.id,
                smeta_item_id=cp.smeta_item_id,
                fsnb_code=cp.fsnb_code,
                name=si.name,
                unit=si.unit,
                quantity=float(si.quantity),
                price=float(cp.price) if cp.price is not None else None,
                total=total,
                ceiling_total=float(si.total_price),
                updated_at=cp.updated_at,
            )
        )
    return prices


async def update_contractor_price(
    project_id: uuid.UUID,
    smeta_item_id: uuid.UUID,
    price: Optional[float],
    user_id: uuid.UUID,
    db: AsyncSession,
) -> ContractorPriceOut:
    result = await db.execute(
        select(ContractorPrice, SmetaItem)
        .join(SmetaItem, ContractorPrice.smeta_item_id == SmetaItem.id)
        .where(
            ContractorPrice.project_id == project_id,
            ContractorPrice.smeta_item_id == smeta_item_id,
        )
    )
    row = result.one_or_none()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Contractor price not found")

    cp, si = row
    cp.price = price
    cp.updated_at = datetime.now(timezone.utc)

    # Sync to user library (cross-DB upsert)
    if cp.fsnb_code:
        lib_result = await db.execute(
            select(ContractorPriceLibrary).where(
                ContractorPriceLibrary.user_id == user_id,
                ContractorPriceLibrary.fsnb_code == cp.fsnb_code,
            )
        )
        lib_entry = lib_result.scalar_one_or_none()
        if lib_entry:
            lib_entry.price = price
            lib_entry.updated_at = datetime.now(timezone.utc)
        else:
            db.add(ContractorPriceLibrary(
                user_id=user_id,
                fsnb_code=cp.fsnb_code,
                name=si.name,
                unit=si.unit,
                price=price,
                updated_at=datetime.now(timezone.utc),
            ))

    await db.commit()
    await db.refresh(cp)

    total = float(cp.price * si.quantity) if cp.price is not None else None
    return ContractorPriceOut(
        id=cp.id,
        smeta_item_id=cp.smeta_item_id,
        fsnb_code=cp.fsnb_code,
        name=si.name,
        unit=si.unit,
        quantity=float(si.quantity),
        price=float(cp.price) if cp.price is not None else None,
        total=total,
        ceiling_total=float(si.total_price),
        updated_at=cp.updated_at,
    )
