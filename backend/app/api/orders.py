from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.app.database import get_db
from backend.app.core.dependencies import require_operator, require_viewer, get_current_user
from backend.app.models.order import Order, OrderLine, PickingTask
from backend.app.models.user import User
from backend.app.schemas.order import (
    OrderCreate, OrderUpdate, OrderOut,
    PickingTaskOut, PickingExecutionRequest
)
from backend.app.services import picking_service
from typing import List, Optional

router = APIRouter()

@router.post("/", response_model=OrderOut, dependencies=[Depends(require_operator)])
async def create_order_endpoint(
    req: OrderCreate,
    db: AsyncSession = Depends(get_db)
):
    lines = [l.dict() for l in req.lines]
    return await picking_service.create_order(
        db,
        warehouse_id=req.warehouse_id,
        order_type=req.order_type,
        customer_name=req.customer_name,
        lines_in=lines,
        priority=req.priority,
        notes=req.notes
    )

@router.get("/", response_model=List[OrderOut], dependencies=[Depends(require_viewer)])
async def list_orders(db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Order)
        .options(selectinload(Order.lines).selectinload(OrderLine.product))
    )
    return res.scalars().all()

@router.get("/{order_id}", response_model=OrderOut, dependencies=[Depends(require_viewer)])
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Order)
        .options(
            selectinload(Order.lines)
            .selectinload(OrderLine.product),
            selectinload(Order.lines)
            .selectinload(OrderLine.location),
            selectinload(Order.lines)
            .selectinload(OrderLine.lot),
            selectinload(Order.lines)
            .selectinload(OrderLine.picking_tasks)
        )
        .filter(Order.id == order_id)
    )
    order = res.scalars().first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return order

@router.post("/{order_id}/assign", response_model=OrderOut, dependencies=[Depends(require_operator)])
async def assign_order_endpoint(
    order_id: str,
    operator_id: str,
    strategy: Optional[str] = "FIFO",
    db: AsyncSession = Depends(get_db)
):
    return await picking_service.assign_picking_tasks(
        db,
        order_id=order_id,
        assigned_operator_id=operator_id,
        strategy=strategy
    )

@router.get("/picking-tasks/operator/{operator_id}", response_model=List[PickingTaskOut], dependencies=[Depends(require_viewer)])
async def list_operator_tasks(operator_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(PickingTask)
        .options(
            selectinload(PickingTask.product),
            selectinload(PickingTask.from_location),
            selectinload(PickingTask.lot)
        )
        .filter(PickingTask.assigned_to == operator_id, PickingTask.status != "COMPLETED")
    )
    return res.scalars().all()

@router.post("/picking-tasks/{task_id}/execute", response_model=PickingTaskOut, dependencies=[Depends(require_operator)])
async def execute_task_endpoint(
    task_id: str,
    req: PickingExecutionRequest,
    db: AsyncSession = Depends(get_db)
):
    db_task = await picking_service.execute_picking_task(
        db,
        task_id=task_id,
        picked_qty=req.picked_quantity
    )
    # Reload with relations
    res = await db.execute(
        select(PickingTask)
        .options(
            selectinload(PickingTask.product),
            selectinload(PickingTask.from_location),
            selectinload(PickingTask.lot)
        )
        .filter(PickingTask.id == db_task.id)
    )
    return res.scalars().first()
