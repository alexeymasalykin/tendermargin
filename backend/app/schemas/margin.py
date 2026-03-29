from __future__ import annotations

from typing import List

from pydantic import BaseModel


class MarginItem(BaseModel):
    name: str
    code: str
    item_type: str
    unit: str
    quantity: float
    ceiling_price: float
    cost_price: float
    margin: float
    margin_pct: float
    status: str  # "green" >15%, "yellow" 5-15%, "red" <5%, "loss" <0%


class MarginResult(BaseModel):
    total_ceiling: float
    total_cost: float
    total_margin: float
    margin_pct: float
    min_profit: float
    max_discount_pct: float
    floor_price: float
    items: List[MarginItem]
