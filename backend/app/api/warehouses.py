from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.app.database import get_db
from backend.app.core.dependencies import require_supervisor, require_viewer
from backend.app.models.warehouse import Warehouse, Zone, Location
from backend.app.schemas.warehouse import (
    WarehouseCreate, WarehouseUpdate, WarehouseOut,
    ZoneCreate, ZoneUpdate, ZoneOut,
    LocationCreate, LocationUpdate, LocationOut
)
from typing import List

router = APIRouter()

# --- Warehouses ---
@router.post("/", response_model=WarehouseOut, dependencies=[Depends(require_supervisor)])
async def create_warehouse(warehouse_in: WarehouseCreate, db: AsyncSession = Depends(get_db)):
    db_wh = Warehouse(**warehouse_in.dict())
    db.add(db_wh)
    await db.commit()
    await db.refresh(db_wh)
    return db_wh

@router.get("/", response_model=List[WarehouseOut], dependencies=[Depends(require_viewer)])
async def list_warehouses(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Warehouse))
    return res.scalars().all()

@router.get("/{warehouse_id}", response_model=WarehouseOut, dependencies=[Depends(require_viewer)])
async def get_warehouse(warehouse_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Warehouse).filter(Warehouse.id == warehouse_id))
    wh = res.scalars().first()
    if not wh:
        raise HTTPException(status_code=404, detail="Bodega no encontrada")
    return wh

# --- Zones ---
@router.post("/zones", response_model=ZoneOut, dependencies=[Depends(require_supervisor)])
async def create_zone(zone_in: ZoneCreate, db: AsyncSession = Depends(get_db)):
    db_zone = Zone(**zone_in.dict())
    db.add(db_zone)
    await db.commit()
    await db.refresh(db_zone)
    return db_zone

@router.get("/{warehouse_id}/zones", response_model=List[ZoneOut], dependencies=[Depends(require_viewer)])
async def list_zones_by_warehouse(warehouse_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Zone)
        .options(selectinload(Zone.locations))
        .filter(Zone.warehouse_id == warehouse_id)
    )
    return res.scalars().all()

# --- Locations ---
@router.post("/locations", response_model=LocationOut, dependencies=[Depends(require_supervisor)])
async def create_location(loc_in: LocationCreate, db: AsyncSession = Depends(get_db)):
    db_loc = Location(**loc_in.dict())
    db.add(db_loc)
    await db.commit()
    await db.refresh(db_loc)
    return db_loc

@router.get("/zones/{zone_id}/locations", response_model=List[LocationOut], dependencies=[Depends(require_viewer)])
async def list_locations_by_zone(zone_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Location).filter(Location.zone_id == zone_id))
    return res.scalars().all()

@router.get("/locations/all", response_model=List[LocationOut], dependencies=[Depends(require_viewer)])
async def list_all_locations(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Location))
    return res.scalars().all()
