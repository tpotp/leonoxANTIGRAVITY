from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None

class CategoryOut(CategoryBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Product Schemas
class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    barcode: Optional[str] = None
    unit_of_measure: Optional[str] = "UNIDAD"
    weight: Optional[float] = 0.0
    volume: Optional[float] = 0.0
    min_stock: Optional[float] = 0.0
    max_stock: Optional[float] = 0.0
    reorder_point: Optional[float] = 0.0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    barcode: Optional[str] = None
    unit_of_measure: Optional[str] = None
    weight: Optional[float] = None
    volume: Optional[float] = None
    min_stock: Optional[float] = None
    max_stock: Optional[float] = None
    reorder_point: Optional[float] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None

class ProductOut(ProductBase):
    id: str
    is_active: bool
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryOut] = None
    model_config = ConfigDict(from_attributes=True)
