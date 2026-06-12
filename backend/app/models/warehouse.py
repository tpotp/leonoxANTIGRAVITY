from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from backend.app.database import Base

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    zones = relationship("Zone", back_populates="warehouse", cascade="all, delete-orphan")
    stock = relationship("Stock", back_populates="warehouse")

class Zone(Base):
    __tablename__ = "zones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False)  # Unique inside warehouse
    zone_type = Column(String(50), default="STORAGE")  # RECEIVING, STORAGE, PICKING, DISPATCH
    created_at = Column(DateTime, default=datetime.utcnow)

    warehouse = relationship("Warehouse", back_populates="zones")
    locations = relationship("Location", back_populates="zone", cascade="all, delete-orphan", lazy="selectin")

class Location(Base):
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_id = Column(String(36), ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False, index=True)  # e.g., A-01-02-03
    aisle = Column(String(20), nullable=True)
    rack = Column(String(20), nullable=True)
    level = Column(String(20), nullable=True)
    position = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    max_weight = Column(Float, default=1000.0)  # in kg
    max_volume = Column(Float, default=10.0)    # in m3
    current_weight = Column(Float, default=0.0)
    current_volume = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    zone = relationship("Zone", back_populates="locations")
    warehouse = relationship("Warehouse")
    stock = relationship("Stock", back_populates="location")
