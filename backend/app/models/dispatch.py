from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from backend.app.database import Base

class Dispatch(Base):
    __tablename__ = "dispatches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    dispatch_number = Column(String(100), unique=True, nullable=False, index=True)
    carrier = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    status = Column(String(50), default="PENDING")  # PENDING, LOADING, DISPATCHED, DELIVERED, CANCELLED
    dispatched_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = relationship("Warehouse")
    dispatcher = relationship("User")
    lines = relationship("DispatchLine", back_populates="dispatch", cascade="all, delete-orphan", lazy="selectin")

class DispatchLine(Base):
    __tablename__ = "dispatch_lines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dispatch_id = Column(String(36), ForeignKey("dispatches.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Float, nullable=False)
    lot_id = Column(String(36), ForeignKey("lots.id", ondelete="SET NULL"), nullable=True)
    serial_numbers = Column(JSON, nullable=True)  # List of serial strings
    created_at = Column(DateTime, default=datetime.utcnow)

    dispatch = relationship("Dispatch", back_populates="lines")
    order = relationship("Order")
    product = relationship("Product", lazy="selectin")
    lot = relationship("Lot", lazy="selectin")
