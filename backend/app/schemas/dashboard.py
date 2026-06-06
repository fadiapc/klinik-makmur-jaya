from __future__ import annotations

from typing import List
from pydantic import BaseModel

from app.schemas.order import OrderOut

class DailySales(BaseModel):
    date: str
    total_sales: float

class DashboardStatsResponse(BaseModel):
    total_products: int
    active_orders: int
    total_patients: int
    system_health: str
    recent_orders: List[OrderOut]
    sales_chart: List[DailySales]
