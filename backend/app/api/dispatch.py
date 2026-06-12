from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.app.database import get_db
from backend.app.core.dependencies import require_operator, require_viewer, get_current_user
from backend.app.models.dispatch import Dispatch, DispatchLine
from backend.app.models.user import User
from backend.app.schemas.dispatch import DispatchCreate, DispatchOut
from backend.app.services import dispatch_service
from typing import List

router = APIRouter()

@router.post("/", response_model=DispatchOut, dependencies=[Depends(require_operator)])
async def create_dispatch_endpoint(
    req: DispatchCreate,
    db: AsyncSession = Depends(get_db)
):
    return await dispatch_service.create_dispatch(
        db,
        warehouse_id=req.warehouse_id,
        order_ids=req.order_ids,
        carrier=req.carrier,
        tracking_number=req.tracking_number,
        notes=req.notes
    )

@router.get("/", response_model=List[DispatchOut], dependencies=[Depends(require_viewer)])
async def list_dispatches(db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Dispatch)
        .options(selectinload(Dispatch.lines).selectinload(DispatchLine.product))
    )
    return res.scalars().all()

@router.get("/{dispatch_id}", response_model=DispatchOut, dependencies=[Depends(require_viewer)])
async def get_dispatch(dispatch_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Dispatch)
        .options(
            selectinload(Dispatch.lines)
            .selectinload(DispatchLine.product),
            selectinload(Dispatch.lines)
            .selectinload(DispatchLine.lot)
        )
        .filter(Dispatch.id == dispatch_id)
    )
    disp = res.scalars().first()
    if not disp:
        raise HTTPException(status_code=404, detail="Despacho no encontrado")
    return disp

@router.post("/{dispatch_id}/confirm", response_model=DispatchOut, dependencies=[Depends(require_operator)])
async def confirm_dispatch_endpoint(
    dispatch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await dispatch_service.confirm_dispatch(db, dispatch_id, current_user.id)
