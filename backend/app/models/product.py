from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from backend.app.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    parent_id = Column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    category_id = Column(String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    barcode = Column(String(100), nullable=True, index=True)
    unit_of_measure = Column(String(20), default="UNIDAD")  # e.g., UNIDAD, KG, LITROS
    weight = Column(Float, default=0.0)  # in kg
    volume = Column(Float, default=0.0)  # in m3
    min_stock = Column(Float, default=0.0)
    max_stock = Column(Float, default=0.0)
    reorder_point = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="products", lazy="selectin")
    stock = relationship("Stock", back_populates="product")
    lots = relationship("Lot", back_populates="product")
