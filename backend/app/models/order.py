from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from backend.app.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    order_number = Column(String(100), unique=True, nullable=False, index=True)
    order_type = Column(String(50), default="SALES")  # SALES, TRANSFER, INTERNAL
    customer_name = Column(String(100), nullable=True)
    status = Column(String(50), default="PENDING")  # PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, DISPATCHED, CANCELLED
    priority = Column(String(50), default="MEDIUM")   # LOW, MEDIUM, HIGH, URGENT
    assigned_to = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = relationship("Warehouse")
    assignee = relationship("User")
    lines = relationship("OrderLine", back_populates="order", cascade="all, delete-orphan", lazy="selectin")

class OrderLine(Base):
    __tablename__ = "order_lines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    requested_quantity = Column(Float, nullable=False)
    picked_quantity = Column(Float, default=0.0)
    location_id = Column(String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)  # Allocation location
    lot_id = Column(String(36), ForeignKey("lots.id", ondelete="SET NULL"), nullable=True)        # Allocation lot
    status = Column(String(50), default="PENDING")  # PENDING, PICKING, PICKED, SHORT
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="lines")
    product = relationship("Product", lazy="selectin")
    location = relationship("Location", lazy="selectin")
    lot = relationship("Lot", lazy="selectin")
    picking_tasks = relationship("PickingTask", back_populates="order_line", cascade="all, delete-orphan", lazy="selectin")

class PickingTask(Base):
    __tablename__ = "picking_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_line_id = Column(String(36), ForeignKey("order_lines.id", ondelete="CASCADE"), nullable=False)
    assigned_to = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    from_location_id = Column(String(36), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    lot_id = Column(String(36), ForeignKey("lots.id", ondelete="SET NULL"), nullable=True)
    quantity_to_pick = Column(Float, nullable=False)
    quantity_picked = Column(Float, default=0.0)
    status = Column(String(50), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order_line = relationship("OrderLine", back_populates="picking_tasks")
    operator = relationship("User")
    product = relationship("Product", lazy="selectin")
    from_location = relationship("Location", lazy="selectin")
    lot = relationship("Lot", lazy="selectin")
