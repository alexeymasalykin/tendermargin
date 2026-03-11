from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=5000)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)


class SmetaProgress(BaseModel):
    status: str  # "not_started" | "completed"
    item_count: int = 0
    total_sum: float = 0.0


class MaterialsProgress(BaseModel):
    status: str  # "not_started" | "in_progress" | "completed"
    filled: int = 0
    total: int = 0


class ContractorProgress(BaseModel):
    status: str  # "not_started" | "in_progress" | "completed"
    filled: int = 0
    total: int = 0


class PricelistProgress(BaseModel):
    status: str  # "not_started" | "in_progress" | "completed"


class MarginProgress(BaseModel):
    available: bool
    margin_pct: Optional[float] = None


class ProjectProgress(BaseModel):
    smeta: SmetaProgress
    materials: MaterialsProgress
    contractor: ContractorProgress
    pricelist: PricelistProgress
    margin: MarginProgress


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetail(ProjectOut):
    progress: ProjectProgress
