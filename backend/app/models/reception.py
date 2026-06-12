from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from backend.app.database import Base

class Reception(Base):
    __tablename__ = "receptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    reference_number = Column(String(100), unique=True, nullable=False, index=True)
    supplier_name = Column(String(100), nullable=False)
    status = Column(String(50), default="DRAFT")  # DRAFT, IN_PROGRESS, COMPLETED, CANCELLED
    expected_date = Column(DateTime, nullable=True)
    received_date = Column(DateTime, nullable=True)
    received_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = relationship("Warehouse")
    receiver = relationship("User")
    lines = relationship("ReceptionLine", back_populates="reception", cascade="all, delete-orphan", lazy="selectin")

class ReceptionLine(Base):
    __tablename__ = "reception_lines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reception_id = Column(String(36), ForeignKey("receptions.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    expected_quantity = Column(Float, nullable=False)
    received_quantity = Column(Float, default=0.0)
    location_id = Column(String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    lot_id = Column(String(36), ForeignKey("lots.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="PENDING")  # PENDING, PARTIAL, COMPLETE, REJECTED
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reception = relationship("Reception", back_populates="lines")
    product = relationship("Product", lazy="selectin")
    location = relationship("Location", lazy="selectin")
    lot = relationship("Lot", lazy="selectin")
