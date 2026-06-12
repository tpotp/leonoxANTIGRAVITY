from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from backend.app.models.order import Order, OrderLine, PickingTask
from backend.app.models.inventory import Stock, StockMovement
from backend.app.models.alert import Alert
from datetime import datetime, timedelta
from typing import Dict, Any

async def calculate_kpis(db: AsyncSession, warehouse_id: str) -> Dict[str, Any]:
    # 1. Fill Rate (line level)
    lines_query = select(OrderLine).join(Order).filter(Order.warehouse_id == warehouse_id)
    lines_res = await db.execute(lines_query)
    lines = lines_res.scalars().all()
    
    total_lines = len(lines)
    full_lines = sum(1 for l in lines if l.picked_quantity >= l.requested_quantity)
    fill_rate = (full_lines / total_lines * 100.0) if total_lines > 0 else 100.0
    
    # 2. OTIF (Order level: completed or dispatched)
    orders_query = select(Order).filter(Order.warehouse_id == warehouse_id)
    orders_res = await db.execute(orders_query)
    orders = orders_res.scalars().all()
    
    total_orders = len(orders)
    completed_orders = sum(1 for o in orders if o.status in ["COMPLETED", "DISPATCHED"])
    otif = (completed_orders / total_orders * 100.0) if total_orders > 0 else 100.0
    
    # 3. Inventory Accuracy
    # Count stockouts
    stockouts_res = await db.execute(
        select(func.count(Stock.id)).filter(Stock.warehouse_id == warehouse_id, Stock.quantity == 0)
    )
    stockouts_count = stockouts_res.scalar() or 0
    
    # Simple simulated accuracy index based on low stock alerts vs total products
    total_stock_res = await db.execute(
        select(func.count(Stock.id)).filter(Stock.warehouse_id == warehouse_id)
    )
    total_stock_count = total_stock_res.scalar() or 1
    
    low_stock_alerts_res = await db.execute(
        select(func.count(Alert.id)).filter(
            Alert.warehouse_id == warehouse_id,
            Alert.alert_type == "LOW_STOCK",
            Alert.is_resolved == False
        )
    )
    low_stock_count = low_stock_alerts_res.scalar() or 0
    accuracy = max(50.0, 100.0 - (low_stock_count / total_stock_count * 100.0))
    
    # 4. Inventory Rotation (simulated based on movements)
    exits_res = await db.execute(
        select(func.sum(StockMovement.quantity)).filter(
            StockMovement.warehouse_id == warehouse_id,
            StockMovement.movement_type == "EXIT"
        )
    )
    exits_qty = exits_res.scalar() or 0.0
    
    total_qty_res = await db.execute(
        select(func.sum(Stock.quantity)).filter(Stock.warehouse_id == warehouse_id)
    )
    total_qty = total_qty_res.scalar() or 1.0
    rotation = (exits_qty / total_qty) if total_qty > 0 else 0.0
    
    # 5. Productivity (picking tasks per hour)
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    tasks_res = await db.execute(
        select(func.count(PickingTask.id)).filter(
            PickingTask.status == "COMPLETED",
            PickingTask.completed_at >= one_day_ago
        )
    )
    tasks_count = tasks_res.scalar() or 0
    productivity = float(tasks_count) / 24.0  # simple tasks/hour over last 24h
    
    return {
        "fill_rate": round(fill_rate, 2),
        "otif": round(otif, 2),
        "inventory_accuracy": round(accuracy, 2),
        "inventory_rotation": round(rotation, 2),
        "productivity_picking": round(productivity, 2),
        "stockouts_count": int(stockouts_count),
    }

async def get_dashboard_summary(db: AsyncSession, warehouse_id: str) -> Dict[str, Any]:
    kpi = await calculate_kpis(db, warehouse_id)
    
    # Stock by Zone
    zone_query = (
        select(Stock.location_id, Stock.quantity)
        .filter(Stock.warehouse_id == warehouse_id)
    )
    # We will do simple python grouping for convenience
    zone_res = await db.execute(zone_query)
    stock_entries = zone_res.all()
    
    # Fetch recent movements
    mov_query = (
        select(StockMovement)
        .options(selectinload(StockMovement.product))
        .filter(StockMovement.warehouse_id == warehouse_id)
        .order_by(StockMovement.created_at.desc())
        .limit(5)
    )
    mov_res = await db.execute(mov_query)
    recent_movs = mov_res.scalars().all()
    
    # Fetch recent alerts
    alert_query = (
        select(Alert)
        .filter(Alert.warehouse_id == warehouse_id, Alert.is_read == False)
        .order_by(Alert.created_at.desc())
        .limit(5)
    )
    alert_res = await db.execute(alert_query)
    recent_alerts = alert_res.scalars().all()
    
    # Structure simple response
    return {
        "kpis": kpi,
        "recent_alerts": [
            {
                "id": a.id,
                "type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "created_at": a.created_at.isoformat()
            }
            for a in recent_alerts
        ],
        "recent_movements": [
            {
                "id": m.id,
                "sku": m.product.sku if m.product else "N/A",
                "product_name": m.product.name if m.product else "N/A",
                "type": m.movement_type,
                "qty": m.quantity,
                "date": m.created_at.isoformat()
            }
            for m in recent_movs
        ]
    }
