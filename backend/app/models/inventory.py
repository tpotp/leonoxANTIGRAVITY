from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from backend.app.database import Base

class Lot(Base):
    __tablename__ = "lots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    lot_number = Column(String(100), nullable=False)
    manufacture_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    supplier = Column(String(100), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="lots")
    stock = relationship("Stock", back_populates="lot")

class Serial(Base):
    __tablename__ = "serials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    lot_id = Column(String(36), ForeignKey("lots.id", ondelete="SET NULL"), nullable=True)
    serial_number = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="AVAILABLE")  # AVAILABLE, RESERVED, DISPATCHED, DAMAGED
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")
    lot = relationship("Lot")

class Stock(Base):
    __tablename__ = "stock"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(String(36), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    lot_id = Column(String(36), ForeignKey("lots.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Float, default=0.0)
    reserved_quantity = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="stock", lazy="selectin")
    warehouse = relationship("Warehouse", back_populates="stock", lazy="selectin")
    location = relationship("Location", back_populates="stock", lazy="selectin")
    lot = relationship("Lot", back_populates="stock", lazy="selectin")

    @property
    def available_quantity(self) -> float:
        return max(0.0, self.quantity - self.reserved_quantity)

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    from_location_id = Column(String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    to_location_id = Column(String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    lot_id = Column(String(36), ForeignKey("lots.id", ondelete="SET NULL"), nullable=True)
    movement_type = Column(String(50), nullable=False)  # ENTRY, EXIT, TRANSFER, ADJUSTMENT
    quantity = Column(Float, nullable=False)
    reference_type = Column(String(50), nullable=True)   # RECEPTION, ORDER, ADJUSTMENT, TRANSFER
    reference_id = Column(String(36), nullable=True)
    performed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", lazy="selectin")
    warehouse = relationship("Warehouse", lazy="selectin")
    from_location = relationship("Location", foreign_keys=[from_location_id], lazy="selectin")
    to_location = relationship("Location", foreign_keys=[to_location_id], lazy="selectin")
    lot = relationship("Lot", lazy="selectin")
    user = relationship("User")
