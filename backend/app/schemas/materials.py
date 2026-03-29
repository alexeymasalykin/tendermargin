from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel


class MaterialOut(BaseModel):
    id: uuid.UUID
    name: str
    unit: str
    quantity: float
    smeta_total: float
    supplier_price: Optional[float] = None
    supplier_total: Optional[float] = None

    model_config = {"from_attributes": True}
