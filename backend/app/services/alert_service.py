from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from backend.app.models.inventory import Stock, Lot
from backend.app.models.product import Product
from backend.app.models.alert import Alert
from datetime import datetime, timedelta
from typing import List

async def check_and_generate_alerts(db: AsyncSession, warehouse_id: str):
    """
    Scans the inventory and generates alerts for:
    - LOW_STOCK: Total quantity of SKU in warehouse < min_stock
    - OVERSTOCK: Total quantity of SKU in warehouse > max_stock
    - EXPIRING: Lots expiring in less than 30 days
    """
    # 1. LOW_STOCK & OVERSTOCK check
    # Aggregate stock by product
    stock_query = (
        select(Stock.product_id, func.sum(Stock.quantity).label("total_qty"))
        .filter(Stock.warehouse_id == warehouse_id)
        .group_by(Stock.product_id)
    )
    stock_res = await db.execute(stock_query)
    stock_sums = stock_res.all()
    
    for product_id, total_qty in stock_sums:
        prod_res = await db.execute(select(Product).filter(Product.id == product_id))
        product = prod_res.scalars().first()
        if not product:
            continue
            
        # Check low stock
        if product.min_stock > 0 and total_qty < product.min_stock:
            # Check if alert already exists (unresolved)
            alert_exists = await db.execute(
                select(Alert).filter(
                    Alert.warehouse_id == warehouse_id,
                    Alert.product_id == product_id,
                    Alert.alert_type == "LOW_STOCK",
                    Alert.is_resolved == False
                )
            )
            if not alert_exists.scalars().first():
                alert = Alert(
                    warehouse_id=warehouse_id,
                    product_id=product_id,
                    alert_type="LOW_STOCK",
                    severity="WARNING",
                    title="Stock Bajo",
                    message=f"El producto {product.name} (SKU: {product.sku}) está por debajo del mínimo. Stock actual: {total_qty}, Mínimo: {product.min_stock}"
                )
                db.add(alert)
                
        # Check overstock
        if product.max_stock > 0 and total_qty > product.max_stock:
            alert_exists = await db.execute(
                select(Alert).filter(
                    Alert.warehouse_id == warehouse_id,
                    Alert.product_id == product_id,
                    Alert.alert_type == "OVERSTOCK",
                    Alert.is_resolved == False
                )
            )
            if not alert_exists.scalars().first():
                alert = Alert(
                    warehouse_id=warehouse_id,
                    product_id=product_id,
                    alert_type="OVERSTOCK",
                    severity="INFO",
                    title="Sobre Stock",
                    message=f"El producto {product.name} (SKU: {product.sku}) supera el máximo permitido. Stock actual: {total_qty}, Máximo: {product.max_stock}"
                )
                db.add(alert)
                
    # 2. EXPIRING check
    # Find active stock entries with lots expiring within 30 days
    limit_date = datetime.utcnow() + timedelta(days=30)
    expiring_query = (
        select(Stock)
        .join(Lot, Stock.lot_id == Lot.id)
        .filter(
            Stock.warehouse_id == warehouse_id,
            Stock.quantity > 0,
            Lot.expiry_date <= limit_date,
            Lot.expiry_date > datetime.utcnow()
        )
    )
    expiring_res = await db.execute(expiring_query)
    expiring_entries = expiring_res.scalars().all()
    
    for entry in expiring_entries:
        # Load lot and product info
        lot_res = await db.execute(select(Lot).filter(Lot.id == entry.lot_id))
        lot = lot_res.scalars().first()
        prod_res = await db.execute(select(Product).filter(Product.id == entry.product_id))
        product = prod_res.scalars().first()
        
        if lot and product:
            alert_exists = await db.execute(
                select(Alert).filter(
                    Alert.warehouse_id == warehouse_id,
                    Alert.product_id == product.id,
                    Alert.alert_type == "EXPIRING",
                    Alert.message.like(f"%Lote: {lot.lot_number}%"),
                    Alert.is_resolved == False
                )
            )
            if not alert_exists.scalars().first():
                alert = Alert(
                    warehouse_id=warehouse_id,
                    product_id=product.id,
                    alert_type="EXPIRING",
                    severity="CRITICAL",
                    title="Lote Próximo a Vencer",
                    message=f"El lote {lot.lot_number} del producto {product.name} (SKU: {product.sku}) vence el {lot.expiry_date.strftime('%Y-%m-%d')}. Stock en lote: {entry.quantity}"
                )
                db.add(alert)
                
    await db.commit()
