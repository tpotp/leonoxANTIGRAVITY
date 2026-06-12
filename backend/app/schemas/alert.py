from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime
from backend.app.schemas.product import ProductOut

class AlertBase(BaseModel):
    warehouse_id: Optional[str] = None
    alert_type: str  # LOW_STOCK, OVERSTOCK, STAGNANT, EXPIRING, PRODUCTIVITY_DEVIATION
    severity: str    # INFO, WARNING, CRITICAL
    title: str
    message: str
    product_id: Optional[str] = None

class AlertOut(AlertBase):
    id: str
    is_read: bool
    is_resolved: bool
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    product: Optional[ProductOut] = None
    model_config = ConfigDict(from_attributes=True)

class KPISnapshotBase(BaseModel):
    warehouse_id: str
    date: datetime
    metric_name: str
    metric_value: float
    metadata_json: Optional[Any] = None

class KPISnapshotOut(KPISnapshotBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
