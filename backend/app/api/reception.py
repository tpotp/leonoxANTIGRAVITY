from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.app.database import get_db
from backend.app.core.dependencies import require_operator, require_viewer, get_current_user
from backend.app.models.reception import Reception, ReceptionLine
from backend.app.models.user import User
from backend.app.schemas.reception import (
    ReceptionCreate, ReceptionUpdate, ReceptionOut,
    ReceptionLineUpdate, ReceptionLineOut
)
from backend.app.services import reception_service
from typing import List

router = APIRouter()

@router.post("/", response_model=ReceptionOut, dependencies=[Depends(require_operator)])
async def create_reception_endpoint(
    req: ReceptionCreate,
    db: AsyncSession = Depends(get_db)
):
    lines = [l.dict() for l in req.lines]
    return await reception_service.create_reception(
        db,
        warehouse_id=req.warehouse_id,
        supplier_name=req.supplier_name,
        expected_date=req.expected_date,
        lines_in=lines,
        notes=req.notes
    )

@router.get("/", response_model=List[ReceptionOut], dependencies=[Depends(require_viewer)])
async def list_receptions(db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Reception)
        .options(selectinload(Reception.lines).selectinload(ReceptionLine.product))
    )
    return res.scalars().all()

@router.get("/{reception_id}", response_model=ReceptionOut, dependencies=[Depends(require_viewer)])
async def get_reception(reception_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Reception)
        .options(
            selectinload(Reception.lines)
            .selectinload(ReceptionLine.product),
            selectinload(Reception.lines)
            .selectinload(ReceptionLine.location),
            selectinload(Reception.lines)
            .selectinload(ReceptionLine.lot)
        )
        .filter(Reception.id == reception_id)
    )
    rep = res.scalars().first()
    if not rep:
        raise HTTPException(status_code=404, detail="Recepción no encontrada")
    return rep

@router.put("/lines/{line_id}", response_model=ReceptionLineOut, dependencies=[Depends(require_operator)])
async def update_line(
    line_id: str,
    req: ReceptionLineUpdate,
    db: AsyncSession = Depends(get_db)
):
    db_line = await reception_service.update_reception_line(
        db,
        line_id=line_id,
        received_quantity=req.received_quantity,
        location_id=req.location_id,
        lot_id=req.lot_id,
        notes=req.notes
    )
    # Reload for detailed output relations
    res = await db.execute(
        select(ReceptionLine)
        .options(
            selectinload(ReceptionLine.product),
            selectinload(ReceptionLine.location),
            selectinload(ReceptionLine.lot)
        )
        .filter(ReceptionLine.id == db_line.id)
    )
    return res.scalars().first()

@router.post("/{reception_id}/confirm", response_model=ReceptionOut, dependencies=[Depends(require_operator)])
async def confirm_reception_endpoint(
    reception_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await reception_service.confirm_reception(db, reception_id, current_user.id)
