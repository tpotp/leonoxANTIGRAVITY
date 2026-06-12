from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.app.database import get_db
from backend.app.core.dependencies import require_viewer, require_operator, get_current_user
from backend.app.models.inventory import Stock, StockMovement
from backend.app.models.user import User
from backend.app.schemas.inventory import (
    StockOut, StockMovementOut,
    StockAdjustmentRequest, StockTransferRequest
)
from backend.app.services import inventory_service, ai_service
from typing import List, Optional

router = APIRouter()

@router.get("/stock", response_model=List[StockOut], dependencies=[Depends(require_viewer)])
async def get_stock_levels(
    product_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    location_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Stock).options(
        selectinload(Stock.product),
        selectinload(Stock.warehouse),
        selectinload(Stock.location),
        selectinload(Stock.lot)
    )
    if product_id:
        query = query.filter(Stock.product_id == product_id)
    if warehouse_id:
        query = query.filter(Stock.warehouse_id == warehouse_id)
    if location_id:
        query = query.filter(Stock.location_id == location_id)
        
    res = await db.execute(query)
    return res.scalars().all()

@router.get("/movements", response_model=List[StockMovementOut], dependencies=[Depends(require_viewer)])
async def get_stock_movements(
    product_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(StockMovement).options(
        selectinload(StockMovement.product),
        selectinload(StockMovement.from_location),
        selectinload(StockMovement.to_location),
        selectinload(StockMovement.lot)
    ).order_by(StockMovement.created_at.desc())
    
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    if warehouse_id:
        query = query.filter(StockMovement.warehouse_id == warehouse_id)
        
    res = await db.execute(query)
    return res.scalars().all()

@router.post("/adjust", response_model=StockOut, dependencies=[Depends(require_operator)])
async def adjust_stock_endpoint(
    req: StockAdjustmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch stock to know its warehouse
    query = select(Stock).filter(
        Stock.product_id == req.product_id,
        Stock.location_id == req.location_id
    )
    if req.lot_id:
        query = query.filter(Stock.lot_id == req.lot_id)
    res = await db.execute(query)
    stock = res.scalars().first()
    
    # If stock does not exist, we need to locate a location to get the warehouse id
    if not stock:
        from backend.app.models.warehouse import Location
        loc_res = await db.execute(select(Location).filter(Location.id == req.location_id))
        loc = loc_res.scalars().first()
        if not loc:
            raise HTTPException(status_code=404, detail="Ubicación no encontrada")
        warehouse_id = loc.warehouse_id
    else:
        warehouse_id = stock.warehouse_id

    # Adjust
    db_stock = await inventory_service.adjust_stock(
        db,
        product_id=req.product_id,
        warehouse_id=warehouse_id,
        location_id=req.location_id,
        new_quantity=req.new_quantity,
        lot_id=req.lot_id,
        performed_by=current_user.id,
        notes=req.notes
    )
    
    # Reload for response
    ans = await db.execute(
        select(Stock).options(
            selectinload(Stock.product),
            selectinload(Stock.warehouse),
            selectinload(Stock.location),
            selectinload(Stock.lot)
        ).filter(Stock.id == db_stock.id)
    )
    return ans.scalars().first()

@router.post("/transfer", dependencies=[Depends(require_operator)])
async def transfer_stock_endpoint(
    req: StockTransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch warehouse from the source location
    from backend.app.models.warehouse import Location
    loc_res = await db.execute(select(Location).filter(Location.id == req.from_location_id))
    loc = loc_res.scalars().first()
    if not loc:
        raise HTTPException(status_code=404, detail="Ubicación de origen no encontrada")
        
    await inventory_service.transfer_stock(
        db,
        product_id=req.product_id,
        warehouse_id=loc.warehouse_id,
        from_location_id=req.from_location_id,
        to_location_id=req.to_location_id,
        quantity=req.quantity,
        lot_id=req.lot_id,
        performed_by=current_user.id,
        notes=req.notes
    )
    return {"message": "Transferencia realizada con éxito"}

@router.get("/predict/{product_id}/{warehouse_id}", dependencies=[Depends(require_viewer)])
async def predict_demand(
    product_id: str,
    warehouse_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await ai_service.predict_sku_demand(db, product_id, warehouse_id)
