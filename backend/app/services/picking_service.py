from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from backend.app.models.order import Order, OrderLine, PickingTask
from backend.app.models.product import Product
from backend.app.services.inventory_service import allocate_stock_fifo, allocate_stock_fefo
from datetime import datetime
from typing import List, Optional
import uuid

async def create_order(
    db: AsyncSession,
    warehouse_id: str,
    order_type: str,
    customer_name: Optional[str],
    lines_in: List[dict],
    priority: str = "MEDIUM",
    notes: Optional[str] = None
) -> Order:
    ord_num = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    db_order = Order(
        warehouse_id=warehouse_id,
        order_number=ord_num,
        order_type=order_type,
        customer_name=customer_name,
        status="PENDING",
        priority=priority,
        notes=notes,
    )
    db.add(db_order)
    await db.flush()
    
    for line in lines_in:
        db_line = OrderLine(
            order_id=db_order.id,
            product_id=line["product_id"],
            requested_quantity=line["requested_quantity"],
            picked_quantity=0.0,
            status="PENDING",
        )
        db.add(db_line)
        
    await db.commit()
    
    # Reload
    res = await db.execute(
        select(Order)
        .options(selectinload(Order.lines).selectinload(OrderLine.product))
        .filter(Order.id == db_order.id)
    )
    return res.scalars().first()

async def assign_picking_tasks(
    db: AsyncSession,
    order_id: str,
    assigned_operator_id: str,
    strategy: str = "FIFO"
) -> Order:
    res = await db.execute(
        select(Order)
        .options(selectinload(Order.lines).selectinload(OrderLine.product))
        .filter(Order.id == order_id)
    )
    order = res.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if order.status != "PENDING":
        raise HTTPException(status_code=400, detail="La orden ya está asignada o en proceso")
        
    # Allocate stock for each line
    for line in order.lines:
        # Determine allocation strategy
        product = line.product
        # If product has lot tracking and FEFO is selected or product is a food/pharma, use FEFO
        if strategy == "FEFO":
            allocation = await allocate_stock_fefo(db, product.id, order.warehouse_id, line.requested_quantity)
        else:
            allocation = await allocate_stock_fifo(db, product.id, order.warehouse_id, line.requested_quantity)
            
        # Create picking tasks and reserve stock
        for alloc in allocation:
            stock_entry = alloc["stock_entry"]
            pick_qty = alloc["quantity"]
            
            # Reserve in DB
            stock_entry.reserved_quantity += pick_qty
            
            task = PickingTask(
                order_line_id=line.id,
                assigned_to=assigned_operator_id,
                product_id=line.product_id,
                from_location_id=alloc["location_id"],
                lot_id=alloc["lot_id"],
                quantity_to_pick=pick_qty,
                quantity_picked=0.0,
                status="PENDING",
            )
            db.add(task)
            
        line.status = "PICKING"
        
    order.status = "ASSIGNED"
    order.assigned_to = assigned_operator_id
    
    await db.commit()
    
    # Reload
    res = await db.execute(
        select(Order)
        .options(selectinload(Order.lines).selectinload(OrderLine.product))
        .filter(Order.id == order_id)
    )
    return res.scalars().first()

async def execute_picking_task(
    db: AsyncSession,
    task_id: str,
    picked_qty: float,
) -> PickingTask:
    res = await db.execute(
        select(PickingTask)
        .options(selectinload(PickingTask.order_line))
        .filter(PickingTask.id == task_id)
    )
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea de picking no encontrada")
        
    if task.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="La tarea de picking ya ha sido completada")
        
    task.quantity_picked = picked_qty
    task.status = "COMPLETED"
    task.completed_at = datetime.utcnow()
    
    # Update order line
    line = task.order_line
    line.picked_quantity += picked_qty
    
    # Check if all tasks for the order line are finished
    tasks_res = await db.execute(
        select(PickingTask).filter(PickingTask.order_line_id == line.id)
    )
    line_tasks = tasks_res.scalars().all()
    all_done = all(t.status == "COMPLETED" for t in line_tasks)
    
    if all_done:
        if line.picked_quantity >= line.requested_quantity:
            line.status = "PICKED"
        else:
            line.status = "SHORT"
            
    # Check if all lines for the order are finished
    order_res = await db.execute(
        select(Order)
        .options(selectinload(Order.lines))
        .filter(Order.id == line.order_id)
    )
    order = order_res.scalars().first()
    
    order_lines_res = await db.execute(
        select(OrderLine).filter(OrderLine.order_id == order.id)
    )
    order_lines = order_lines_res.scalars().all()
    
    if all(l.status in ["PICKED", "SHORT"] for l in order_lines):
        order.status = "COMPLETED"
        
    await db.commit()
    return task
