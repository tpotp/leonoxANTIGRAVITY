from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from backend.app.models.dispatch import Dispatch, DispatchLine
from backend.app.models.order import Order, OrderLine, PickingTask
from backend.app.models.inventory import Stock
from backend.app.services.inventory_service import remove_stock
from datetime import datetime
from typing import List, Optional
import uuid

async def create_dispatch(
    db: AsyncSession,
    warehouse_id: str,
    order_ids: List[str],
    carrier: Optional[str] = None,
    tracking_number: Optional[str] = None,
    notes: Optional[str] = None
) -> Dispatch:
    disp_num = f"DSP-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    db_dispatch = Dispatch(
        warehouse_id=warehouse_id,
        dispatch_number=disp_num,
        carrier=carrier,
        tracking_number=tracking_number,
        status="PENDING",
        notes=notes,
    )
    db.add(db_dispatch)
    await db.flush()
    
    for order_id in order_ids:
        # Load order lines and picking tasks to create dispatch lines
        order_res = await db.execute(
            select(Order)
            .options(selectinload(Order.lines).selectinload(OrderLine.picking_tasks))
            .filter(Order.id == order_id)
        )
        order = order_res.scalars().first()
        if not order or order.status != "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail=f"La orden {order_id} no existe o no está en estado COMPLETADO (preparada)",
            )
            
        # Create dispatch lines based on picking tasks
        for line in order.lines:
            for task in line.picking_tasks:
                if task.quantity_picked > 0:
                    dispatch_line = DispatchLine(
                        dispatch_id=db_dispatch.id,
                        order_id=order.id,
                        product_id=line.product_id,
                        quantity=task.quantity_picked,
                        lot_id=task.lot_id,
                    )
                    db.add(dispatch_line)
                    
        order.status = "DISPATCHED"
        
    await db.commit()
    
    # Reload
    res = await db.execute(
        select(Dispatch)
        .options(selectinload(Dispatch.lines).selectinload(DispatchLine.product))
        .filter(Dispatch.id == db_dispatch.id)
    )
    return res.scalars().first()

async def confirm_dispatch(
    db: AsyncSession,
    dispatch_id: str,
    performed_by: str
) -> Dispatch:
    res = await db.execute(
        select(Dispatch)
        .options(
            selectinload(Dispatch.lines)
            .selectinload(DispatchLine.order)
            .selectinload(Order.lines)
            .selectinload(OrderLine.picking_tasks)
        )
        .filter(Dispatch.id == dispatch_id)
    )
    dispatch = res.scalars().first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Despacho no encontrado")
        
    if dispatch.status == "DISPATCHED":
        raise HTTPException(status_code=400, detail="El despacho ya fue confirmado anteriormente")
        
    # Deduct stock and release reservations
    for line in dispatch.lines:
        # Fetch the corresponding picking tasks to know from which location to deduct
        order_res = await db.execute(
            select(Order)
            .options(selectinload(Order.lines).selectinload(OrderLine.picking_tasks))
            .filter(Order.id == line.order_id)
        )
        order = order_res.scalars().first()
        
        for order_line in order.lines:
            if order_line.product_id == line.product_id:
                for task in order_line.picking_tasks:
                    if task.lot_id == line.lot_id and task.quantity_picked > 0:
                        # 1. Release reservation from Stock table
                        stock_res = await db.execute(
                            select(Stock).filter(
                                Stock.product_id == line.product_id,
                                Stock.location_id == task.from_location_id,
                                Stock.lot_id == task.lot_id,
                            )
                        )
                        stock = stock_res.scalars().first()
                        if stock:
                            # Safely subtract reservation
                            stock.reserved_quantity = max(0.0, stock.reserved_quantity - task.quantity_picked)
                            
                        # 2. Subtract actual stock and write stock movement EXIT log
                        await remove_stock(
                            db,
                            product_id=line.product_id,
                            warehouse_id=dispatch.warehouse_id,
                            location_id=task.from_location_id,
                            quantity=task.quantity_picked,
                            lot_id=task.lot_id,
                            movement_type="EXIT",
                            reference_type="ORDER",
                            reference_id=line.order_id,
                            performed_by=performed_by,
                            notes=f"Despacho {dispatch.dispatch_number}",
                        )
                        
    dispatch.status = "DISPATCHED"
    dispatch.dispatched_by = performed_by
    dispatch.dispatched_at = datetime.utcnow()
    
    await db.commit()
    return dispatch
