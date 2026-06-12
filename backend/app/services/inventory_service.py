from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from backend.app.models.inventory import Stock, StockMovement, Lot
from backend.app.models.product import Product
from backend.app.models.warehouse import Location
from datetime import datetime
from typing import Optional, List

async def add_stock(
    db: AsyncSession,
    product_id: str,
    warehouse_id: str,
    location_id: str,
    quantity: float,
    lot_id: Optional[str] = None,
    movement_type: str = "ENTRY",
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
    performed_by: Optional[str] = None,
    notes: Optional[str] = None,
) -> Stock:
    # 1. Fetch product & location to update weight/volume
    product_res = await db.execute(select(Product).filter(Product.id == product_id))
    product = product_res.scalars().first()
    location_res = await db.execute(select(Location).filter(Location.id == location_id))
    location = location_res.scalars().first()
    
    if not product or not location:
        raise HTTPException(status_code=404, detail="Producto o ubicación no encontrada")
        
    # Check weight and volume limits
    added_weight = product.weight * quantity
    added_volume = product.volume * quantity
    
    if location.current_weight + added_weight > location.max_weight:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Capacidad de peso excedida en ubicación {location.code}. Límite: {location.max_weight} kg",
        )
    if location.current_volume + added_volume > location.max_volume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Capacidad de volumen excedida en ubicación {location.code}. Límite: {location.max_volume} m3",
        )
        
    # 2. Get or create stock entry
    query = select(Stock).filter(
        Stock.product_id == product_id,
        Stock.warehouse_id == warehouse_id,
        Stock.location_id == location_id,
    )
    if lot_id:
        query = query.filter(Stock.lot_id == lot_id)
    else:
        query = query.filter(Stock.lot_id == None)
        
    stock_res = await db.execute(query)
    stock = stock_res.scalars().first()
    
    if stock:
        stock.quantity += quantity
    else:
        stock = Stock(
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            lot_id=lot_id,
            quantity=quantity,
            reserved_quantity=0.0,
        )
        db.add(stock)
        
    # 3. Update location current loads
    location.current_weight += added_weight
    location.current_volume += added_volume
    
    # 4. Create movement record
    movement = StockMovement(
        product_id=product_id,
        warehouse_id=warehouse_id,
        to_location_id=location_id,
        lot_id=lot_id,
        movement_type=movement_type,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        performed_by=performed_by,
        notes=notes,
    )
    db.add(movement)
    
    await db.flush()
    return stock

async def remove_stock(
    db: AsyncSession,
    product_id: str,
    warehouse_id: str,
    location_id: str,
    quantity: float,
    lot_id: Optional[str] = None,
    movement_type: str = "EXIT",
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
    performed_by: Optional[str] = None,
    notes: Optional[str] = None,
) -> Stock:
    # 1. Fetch stock entry
    query = select(Stock).filter(
        Stock.product_id == product_id,
        Stock.warehouse_id == warehouse_id,
        Stock.location_id == location_id,
    )
    if lot_id:
        query = query.filter(Stock.lot_id == lot_id)
    else:
        query = query.filter(Stock.lot_id == None)
        
    stock_res = await db.execute(query)
    stock = stock_res.scalars().first()
    
    if not stock or stock.quantity < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock insuficiente en la ubicación indicada",
        )
        
    # Check reservation limits
    if stock.quantity - stock.reserved_quantity < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock disponible insuficiente (hay cantidades reservadas)",
        )
        
    # 2. Subtract quantity
    stock.quantity -= quantity
    
    # 3. Update location current loads
    product_res = await db.execute(select(Product).filter(Product.id == product_id))
    product = product_res.scalars().first()
    location_res = await db.execute(select(Location).filter(Location.id == location_id))
    location = location_res.scalars().first()
    
    if product and location:
        subtracted_weight = product.weight * quantity
        subtracted_volume = product.volume * quantity
        location.current_weight = max(0.0, location.current_weight - subtracted_weight)
        location.current_volume = max(0.0, location.current_volume - subtracted_volume)
        
    # If quantity is 0, delete stock row to clean up
    if stock.quantity <= 0:
        await db.delete(stock)
        
    # 4. Create movement record
    movement = StockMovement(
        product_id=product_id,
        warehouse_id=warehouse_id,
        from_location_id=location_id,
        lot_id=lot_id,
        movement_type=movement_type,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        performed_by=performed_by,
        notes=notes,
    )
    db.add(movement)
    
    await db.flush()
    return stock

async def transfer_stock(
    db: AsyncSession,
    product_id: str,
    warehouse_id: str,
    from_location_id: str,
    to_location_id: str,
    quantity: float,
    lot_id: Optional[str] = None,
    performed_by: Optional[str] = None,
    notes: Optional[str] = None,
):
    # Withdraw from source
    await remove_stock(
        db,
        product_id=product_id,
        warehouse_id=warehouse_id,
        location_id=from_location_id,
        quantity=quantity,
        lot_id=lot_id,
        movement_type="TRANSFER",
        reference_type="TRANSFER",
        performed_by=performed_by,
        notes=f"Retiro de transferencia. {notes or ''}",
    )
    
    # Put in target
    await add_stock(
        db,
        product_id=product_id,
        warehouse_id=warehouse_id,
        location_id=to_location_id,
        quantity=quantity,
        lot_id=lot_id,
        movement_type="TRANSFER",
        reference_type="TRANSFER",
        performed_by=performed_by,
        notes=f"Ingreso de transferencia. {notes or ''}",
    )

async def adjust_stock(
    db: AsyncSession,
    product_id: str,
    warehouse_id: str,
    location_id: str,
    new_quantity: float,
    lot_id: Optional[str] = None,
    performed_by: Optional[str] = None,
    notes: Optional[str] = None,
) -> Stock:
    query = select(Stock).filter(
        Stock.product_id == product_id,
        Stock.warehouse_id == warehouse_id,
        Stock.location_id == location_id,
    )
    if lot_id:
        query = query.filter(Stock.lot_id == lot_id)
    else:
        query = query.filter(Stock.lot_id == None)
        
    stock_res = await db.execute(query)
    stock = stock_res.scalars().first()
    
    old_qty = stock.quantity if stock else 0.0
    difference = new_quantity - old_qty
    
    if difference > 0:
        return await add_stock(
            db,
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            quantity=difference,
            lot_id=lot_id,
            movement_type="ADJUSTMENT",
            reference_type="ADJUSTMENT",
            performed_by=performed_by,
            notes=f"Ajuste positivo. {notes or ''}",
        )
    elif difference < 0:
        return await remove_stock(
            db,
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            quantity=abs(difference),
            lot_id=lot_id,
            movement_type="ADJUSTMENT",
            reference_type="ADJUSTMENT",
            performed_by=performed_by,
            notes=f"Ajuste negativo. {notes or ''}",
        )
        
    return stock

# FIFO / FEFO Allocation Engine
async def allocate_stock_fifo(
    db: AsyncSession,
    product_id: str,
    warehouse_id: str,
    required_qty: float,
) -> List[dict]:
    """
    Allocates stock using FIFO strategy (oldest stock first, sorted by created_at).
    Returns a list of dicts with keys: location_id, lot_id, quantity.
    """
    query = (
        select(Stock)
        .filter(Stock.product_id == product_id, Stock.warehouse_id == warehouse_id)
        .order_by(Stock.created_at.asc())  # Older first
    )
    res = await db.execute(query)
    stock_entries = res.scalars().all()
    
    allocation = []
    qty_remaining = required_qty
    
    for entry in stock_entries:
        if qty_remaining <= 0:
            break
        available = entry.quantity - entry.reserved_quantity
        if available <= 0:
            continue
            
        pick_qty = min(available, qty_remaining)
        allocation.append({
            "location_id": entry.location_id,
            "lot_id": entry.lot_id,
            "quantity": pick_qty,
            "stock_entry": entry
        })
        qty_remaining -= pick_qty
        
    if qty_remaining > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock disponible insuficiente para FIFO. Faltan {qty_remaining} unidades",
        )
        
    return allocation

async def allocate_stock_fefo(
    db: AsyncSession,
    product_id: str,
    warehouse_id: str,
    required_qty: float,
) -> List[dict]:
    """
    Allocates stock using FEFO strategy (earliest expiry first, sorted by lot.expiry_date).
    If no lot or lot has no expiry, falls back to created_at.
    """
    # Join with Lot to sort by expiry date
    query = (
        select(Stock)
        .outerjoin(Lot, Stock.lot_id == Lot.id)
        .filter(Stock.product_id == product_id, Stock.warehouse_id == warehouse_id)
        .order_by(Lot.expiry_date.asc(), Stock.created_at.asc())
    )
    res = await db.execute(query)
    stock_entries = res.scalars().all()
    
    allocation = []
    qty_remaining = required_qty
    
    for entry in stock_entries:
        if qty_remaining <= 0:
            break
        available = entry.quantity - entry.reserved_quantity
        if available <= 0:
            continue
            
        pick_qty = min(available, qty_remaining)
        allocation.append({
            "location_id": entry.location_id,
            "lot_id": entry.lot_id,
            "quantity": pick_qty,
            "stock_entry": entry
        })
        qty_remaining -= pick_qty
        
    if qty_remaining > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock disponible insuficiente para FEFO. Faltan {qty_remaining} unidades",
        )
        
    return allocation
