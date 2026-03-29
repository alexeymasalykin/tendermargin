from __future__ import annotations

import uuid
from typing import List

from pydantic import BaseModel


class SmetaUploadResult(BaseModel):
    upload_id: str
    filename: str


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
