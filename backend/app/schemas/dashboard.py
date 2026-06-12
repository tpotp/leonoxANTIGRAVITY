from pydantic import BaseModel
from typing import Dict, Any, List

class KPISummary(BaseModel):
    fill_rate: float
    otif: float
    inventory_accuracy: float
    inventory_rotation: float
    productivity_picking: float  # picks per hour
    stockouts_count: int

class DashboardData(BaseModel):
    kpis: KPISummary
    recent_alerts: List[Any]
    recent_movements: List[Any]
    stock_by_zone: Dict[str, float]
    monthly_activity: Dict[str, Dict[str, float]]  # e.g., {"2026-06": {"entries": 120, "exits": 90}}
