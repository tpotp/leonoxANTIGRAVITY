from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from backend.app.schemas.product import ProductOut
from backend.app.schemas.warehouse import WarehouseOut, LocationOut

# Lot Schemas
class LotBase(BaseModel):
    lot_number: str
    manufacture_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    supplier: Optional[str] = None
    notes: Optional[str] = None

class LotCreate(LotBase):
    product_id: str

class LotOut(LotBase):
    id: str
    product_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Serial Schemas
class SerialBase(BaseModel):
    serial_number: str
    status: Optional[str] = "AVAILABLE"  # AVAILABLE, RESERVED, DISPATCHED, DAMAGED

class SerialCreate(SerialBase):
    product_id: str
    lot_id: Optional[str] = None

class SerialOut(SerialBase):
    id: str
    product_id: str
    lot_id: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Stock Schemas
class StockBase(BaseModel):
    product_id: str
    warehouse_id: str
    location_id: str
    lot_id: Optional[str] = None
    quantity: float
    reserved_quantity: Optional[float] = 0.0

class StockCreate(StockBase):
    pass

class StockOut(StockBase):
    id: str
    available_quantity: float
    created_at: datetime
    updated_at: datetime
    product: ProductOut
    warehouse: WarehouseOut
    location: LocationOut
    lot: Optional[LotOut] = None
    model_config = ConfigDict(from_attributes=True)

# StockMovement Schemas
class StockMovementBase(BaseModel):
    product_id: str
    warehouse_id: str
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    lot_id: Optional[str] = None
    movement_type: str  # ENTRY, EXIT, TRANSFER, ADJUSTMENT
    quantity: float
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None

class StockMovementCreate(StockMovementBase):
    pass

class StockMovementOut(StockMovementBase):
    id: str
    performed_by: Optional[str] = None
    created_at: datetime
    product: ProductOut
    from_location: Optional[LocationOut] = None
    to_location: Optional[LocationOut] = None
    lot: Optional[LotOut] = None
    model_config = ConfigDict(from_attributes=True)

# Custom Operations Schemas
class StockAdjustmentRequest(BaseModel):
    product_id: str
    location_id: str
    lot_id: Optional[str] = None
    new_quantity: float
    notes: Optional[str] = None

class StockTransferRequest(BaseModel):
    product_id: str
    from_location_id: str
    to_location_id: str
    lot_id: Optional[str] = None
    quantity: float
    notes: Optional[str] = None
