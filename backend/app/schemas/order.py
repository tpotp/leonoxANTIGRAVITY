from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from backend.app.schemas.product import ProductOut
from backend.app.schemas.warehouse import LocationOut
from backend.app.schemas.inventory import LotOut

# OrderLine Schemas
class OrderLineBase(BaseModel):
    product_id: str
    requested_quantity: float

class OrderLineCreate(OrderLineBase):
    pass

class OrderLineOut(OrderLineBase):
    id: str
    order_id: str
    picked_quantity: float
    location_id: Optional[str] = None
    lot_id: Optional[str] = None
    status: str
    created_at: datetime
    product: ProductOut
    location: Optional[LocationOut] = None
    lot: Optional[LotOut] = None
    model_config = ConfigDict(from_attributes=True)

# PickingTask Schemas
class PickingTaskBase(BaseModel):
    order_line_id: str
    assigned_to: str
    product_id: str
    from_location_id: str
    lot_id: Optional[str] = None
    quantity_to_pick: float

class PickingTaskCreate(PickingTaskBase):
    pass

class PickingTaskOut(PickingTaskBase):
    id: str
    quantity_picked: float
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    product: ProductOut
    from_location: LocationOut
    lot: Optional[LotOut] = None
    model_config = ConfigDict(from_attributes=True)

class PickingExecutionRequest(BaseModel):
    picked_quantity: float

# Order Schemas
class OrderBase(BaseModel):
    warehouse_id: str
    order_type: Optional[str] = "SALES"  # SALES, TRANSFER, INTERNAL
    customer_name: Optional[str] = None
    priority: Optional[str] = "MEDIUM"   # LOW, MEDIUM, HIGH, URGENT
    notes: Optional[str] = None

class OrderCreate(OrderBase):
    lines: List[OrderLineCreate]

class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None

class OrderOut(BaseModel):
    id: str
    warehouse_id: str
    order_number: str
    order_type: str
    customer_name: Optional[str] = None
    status: str
    priority: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lines: List[OrderLineOut] = []
    model_config = ConfigDict(from_attributes=True)
