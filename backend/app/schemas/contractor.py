from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ContractorPriceOut(BaseModel):
    id: uuid.UUID
    smeta_item_id: uuid.UUID
    fsnb_code: str
    name: str
    unit: str
    quantity: float
    price: Optional[float] = None
    total: Optional[float] = None
    ceiling_total: float = 0.0
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContractorPriceUpdate(BaseModel):
    smeta_item_id: uuid.UUID
    price: Optional[float] = Field(None, ge=0)


class ContractorPriceBatchUpdate(BaseModel):
    prices: List[ContractorPriceUpdate]


class ContractorPriceSingleUpdate(BaseModel):
    price: Optional[float] = Field(None, ge=0)
