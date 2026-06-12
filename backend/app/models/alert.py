from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from backend.app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # LOW_STOCK, OVERSTOCK, STAGNANT, EXPIRING, PRODUCTIVITY_DEVIATION
    severity = Column(String(50), default="INFO")    # INFO, WARNING, CRITICAL
    title = Column(String(200), nullable=False)
    message = Column(String(500), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    warehouse = relationship("Warehouse")
    product = relationship("Product", lazy="selectin")
    resolver = relationship("User")

class KPISnapshot(Base):
    __tablename__ = "kpi_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    metric_name = Column(String(100), nullable=False)  # e.g., FILL_RATE, OTIF, ACCURACY, ROTATION, PRODUCTIVITY
    metric_value = Column(Float, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    warehouse = relationship("Warehouse")
