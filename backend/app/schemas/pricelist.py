from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PricelistUploadResult(BaseModel):
    upload_id: uuid.UUID
    filename: str


class PricelistStructure(BaseModel):
    name_column: Optional[str] = None
    unit_column: Optional[str] = None
    price_column: Optional[str] = None
    raw_columns: List[str] = []
    extra: Dict[str, Any] = {}


class PricelistMapRequest(BaseModel):
    structure: PricelistStructure


class PricelistMapStarted(BaseModel):
    task_id: str


class PricelistMatchPartial(BaseModel):
    material_name: str
    supplier_name: Optional[str] = None
    supplier_price: Optional[float] = None
    confidence: Optional[float] = None
    status: str = "pending"


class PricelistMapStatus(BaseModel):
    status: str   # "running" | "completed" | "failed"
    progress: int
    total: int
    matches: List[PricelistMatchPartial] = []
    error: Optional[str] = None


class PricelistMatchOut(BaseModel):
    id: uuid.UUID
    material_id: uuid.UUID
    material_name: str = ""
    supplier_name: Optional[str] = None
    supplier_price: Optional[float] = None
    confidence: Optional[float] = None
    status: str
    updated_at: datetime


class PricelistMatchUpdate(BaseModel):
    id: uuid.UUID
    supplier_price: Optional[float] = Field(None, ge=0)
    status: Optional[str] = None


class PricelistMatchBatchUpdate(BaseModel):
    updates: List[PricelistMatchUpdate]
