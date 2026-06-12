from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from backend.app.schemas.product import ProductOut
from backend.app.schemas.warehouse import LocationOut
from backend.app.schemas.inventory import LotOut

# ReceptionLine Schemas
class ReceptionLineBase(BaseModel):
    product_id: str
    expected_quantity: float
    notes: Optional[str] = None

class ReceptionLineCreate(ReceptionLineBase):
    pass

class ReceptionLineUpdate(BaseModel):
    received_quantity: Optional[float] = None
    location_id: Optional[str] = None
    lot_id: Optional[str] = None
    status: Optional[str] = None  # PENDING, PARTIAL, COMPLETE, REJECTED
    notes: Optional[str] = None

class ReceptionLineOut(ReceptionLineBase):
    id: str
    reception_id: str
    received_quantity: float
    location_id: Optional[str] = None
    lot_id: Optional[str] = None
    status: str
    created_at: datetime
    product: ProductOut
    location: Optional[LocationOut] = None
    lot: Optional[LotOut] = None
    model_config = ConfigDict(from_attributes=True)

# Reception Schemas
class ReceptionBase(BaseModel):
    warehouse_id: str
    reference_number: str
    supplier_name: str
    expected_date: Optional[datetime] = None
    notes: Optional[str] = None

class ReceptionCreate(BaseModel):
    warehouse_id: str
    supplier_name: str
    expected_date: Optional[datetime] = None
    notes: Optional[str] = None
    lines: List[ReceptionLineCreate]

class ReceptionUpdate(BaseModel):
    supplier_name: Optional[str] = None
    expected_date: Optional[datetime] = None
    status: Optional[str] = None  # DRAFT, IN_PROGRESS, COMPLETED, CANCELLED
    notes: Optional[str] = None

class ReceptionOut(ReceptionBase):
    id: str
    status: str
    received_date: Optional[datetime] = None
    received_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lines: List[ReceptionLineOut] = []
    model_config = ConfigDict(from_attributes=True)
