from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from backend.app.schemas.product import ProductOut
from backend.app.schemas.inventory import LotOut

# DispatchLine Schemas
class DispatchLineBase(BaseModel):
    order_id: str
    product_id: str
    quantity: float
    lot_id: Optional[str] = None
    serial_numbers: Optional[List[str]] = None

class DispatchLineCreate(DispatchLineBase):
    pass

class DispatchLineOut(DispatchLineBase):
    id: str
    dispatch_id: str
    created_at: datetime
    product: ProductOut
    lot: Optional[LotOut] = None
    model_config = ConfigDict(from_attributes=True)

# Dispatch Schemas
class DispatchBase(BaseModel):
    warehouse_id: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

class DispatchCreate(BaseModel):
    warehouse_id: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    order_ids: List[str]

class DispatchUpdate(BaseModel):
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    status: Optional[str] = None  # PENDING, LOADING, DISPATCHED, DELIVERED, CANCELLED
    notes: Optional[str] = None

class DispatchOut(DispatchBase):
    id: str
    dispatch_number: str
    status: str
    dispatched_by: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lines: List[DispatchLineOut] = []
    model_config = ConfigDict(from_attributes=True)
