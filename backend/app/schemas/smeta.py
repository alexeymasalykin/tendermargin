from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SmetaUploadResult(BaseModel):
    item_count: int
    total_sum: float


class SmetaItemOut(BaseModel):
    id: uuid.UUID
    number: int
    code: str
    name: str
    unit: str
    quantity: float
    unit_price: float
    total_price: float
    item_type: str
    section: str

    model_config = {"from_attributes": True}


class SmetaItemsPage(BaseModel):
    items: List[SmetaItemOut]
    total: int
    page: int
    page_size: int
    pages: int
