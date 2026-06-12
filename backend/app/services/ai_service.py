from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from backend.app.models.inventory import Stock, StockMovement
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.alert import Alert
from datetime import datetime, timedelta
from typing import Dict, Any, List

async def predict_sku_demand(db: AsyncSession, product_id: str, warehouse_id: str, days_to_predict: int = 30) -> Dict[str, Any]:
    """
    Predicts future demand using historical stock movement data.
    Implements a simple moving average with trend calculation.
    """
    # Get last 30 days of exit movements
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    query = select(StockMovement).filter(
        StockMovement.product_id == product_id,
        StockMovement.warehouse_id == warehouse_id,
        StockMovement.movement_type == "EXIT",
        StockMovement.created_at >= thirty_days_ago
    )
    res = await db.execute(query)
    movements = res.scalars().all()
    
    total_exits = sum(m.quantity for m in movements)
    daily_average = total_exits / 30.0
    
    # Calculate simple trend (first 15 days vs last 15 days)
    fifteen_days_ago = datetime.utcnow() - timedelta(days=15)
    first_half = sum(m.quantity for m in movements if m.created_at < fifteen_days_ago)
    second_half = sum(m.quantity for m in movements if m.created_at >= fifteen_days_ago)
    
    trend_factor = 1.0
    if first_half > 0:
        trend_factor = max(0.5, min(2.0, second_half / first_half))
        
    predicted_demand = daily_average * days_to_predict * trend_factor
    
    # Current stock
    stock_res = await db.execute(
        select(func.sum(Stock.quantity)).filter(
            Stock.product_id == product_id,
            Stock.warehouse_id == warehouse_id
        )
    )
    current_stock = stock_res.scalar() or 0.0
    
    days_left = (current_stock / daily_average) if daily_average > 0 else 999.0
    risk_of_stockout = days_left < days_to_predict
    
    # Fetch product info
    prod_res = await db.execute(select(Product).filter(Product.id == product_id))
    product = prod_res.scalars().first()
    
    return {
        "sku": product.sku if product else "N/A",
        "product_name": product.name if product else "N/A",
        "current_stock": current_stock,
        "daily_average_consumption": round(daily_average, 2),
        "predicted_demand_next_30_days": round(predicted_demand, 2),
        "estimated_days_of_stock": round(days_left, 1) if days_left < 999.0 else "999+",
        "risk_of_stockout": risk_of_stockout,
        "recommended_reorder_qty": round(max(0.0, predicted_demand - current_stock), 2)
    }

async def process_nlp_assistant_query(db: AsyncSession, warehouse_id: str, query_text: str) -> str:
    """
    Parses natural language requests and returns text responses using structural rules.
    Acts as the intelligent WMS Assistant.
    """
    query_text = query_text.lower()
    
    if "quiebre" in query_text or "stockout" in query_text or "bajo stock" in query_text:
        # Check low stock products
        alerts_res = await db.execute(
            select(Alert).filter(
                Alert.warehouse_id == warehouse_id,
                Alert.alert_type == "LOW_STOCK",
                Alert.is_resolved == False
            )
        )
        alerts = alerts_res.scalars().all()
        if not alerts:
            return "¡Excelente noticia! Actualmente ningún SKU presenta riesgo inminente de quiebre de stock en esta bodega."
        
        reply = "Los siguientes SKU presentan riesgo de quiebre:\n"
        for idx, alert in enumerate(alerts, 1):
            reply += f"{idx}. {alert.message}\n"
        return reply
        
    elif "rotación" in query_text or "lento" in query_text or "inmovilizado" in query_text:
        # Check stagnant products
        products_res = await db.execute(select(Product).filter(Product.is_active == True))
        products = products_res.scalars().all()
        
        stagnant = []
        for p in products:
            # Check if there are exits in the last 30 days
            exits_res = await db.execute(
                select(func.count(StockMovement.id)).filter(
                    StockMovement.product_id == p.id,
                    StockMovement.warehouse_id == warehouse_id,
                    StockMovement.movement_type == "EXIT",
                    StockMovement.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            )
            count = exits_res.scalar() or 0
            if count == 0:
                stagnant.append(p)
                
        if not stagnant:
            return "Todos los productos han tenido rotación en los últimos 30 días."
            
        reply = "Los siguientes productos han tenido nula o muy baja rotación en los últimos 30 días:\n"
        for idx, p in enumerate(stagnant[:5], 1):
            reply += f"{idx}. {p.name} (SKU: {p.sku}) - Sin registros de salida recientes.\n"
        if len(stagnant) > 5:
            reply += f"...y {len(stagnant) - 5} productos más."
        return reply
        
    elif "atraso" in query_text or "pendiente" in query_text or "retraso" in query_text:
        # Check pending/delayed orders
        orders_res = await db.execute(
            select(Order).filter(
                Order.warehouse_id == warehouse_id,
                Order.status.in_(["PENDING", "ASSIGNED", "IN_PROGRESS"])
            )
        )
        orders = orders_res.scalars().all()
        if not orders:
            return "No hay órdenes pendientes en este momento. ¡Todas las tareas están al día!"
            
        reply = f"Hay {len(orders)} órdenes en preparación o pendientes:\n"
        for idx, o in enumerate(orders[:5], 1):
            reply += f"{idx}. Orden {o.order_number} - Estado: {o.status}, Prioridad: {o.priority}, Cliente: {o.customer_name or 'N/A'}\n"
        return reply
        
    return ("Hola, soy tu Asistente Inteligente de SmartWMS AI. "
            "Puedo responder preguntas como:\n"
            "- '¿Qué SKU presentan riesgo de quiebre?'\n"
            "- '¿Qué productos tienen baja rotación?'\n"
            "- '¿Qué pedidos tienen riesgo de atraso?'")
