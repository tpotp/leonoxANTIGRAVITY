from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# Location Schemas
class LocationBase(BaseModel):
    code: str
    aisle: Optional[str] = None
    rack: Optional[str] = None
    level: Optional[str] = None
    position: Optional[str] = None
    max_weight: Optional[float] = 1000.0
    max_volume: Optional[float] = 10.0

class LocationCreate(LocationBase):
    zone_id: str
    warehouse_id: str

class LocationUpdate(BaseModel):
    code: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    level: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None
    max_weight: Optional[float] = None
    max_volume: Optional[float] = None

class LocationOut(LocationBase):
    id: str
    zone_id: str
    warehouse_id: str
    is_active: bool
    current_weight: float
    current_volume: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Zone Schemas
class ZoneBase(BaseModel):
    name: str
    code: str
    zone_type: Optional[str] = "STORAGE"  # RECEIVING, STORAGE, PICKING, DISPATCH

class ZoneCreate(ZoneBase):
    warehouse_id: str

class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    zone_type: Optional[str] = None

class ZoneOut(ZoneBase):
    id: str
    warehouse_id: str
    created_at: datetime
    locations: List[LocationOut] = []
    model_config = ConfigDict(from_attributes=True)

# Warehouse Schemas
class WarehouseBase(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None

class WarehouseOut(WarehouseBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
