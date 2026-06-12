from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from backend.app.models.reception import Reception, ReceptionLine
from backend.app.services.inventory_service import add_stock
from datetime import datetime
from typing import List, Optional
import uuid

async def create_reception(
    db: AsyncSession,
    warehouse_id: str,
    supplier_name: str,
    expected_date: Optional[datetime],
    lines_in: List[dict],
    notes: Optional[str] = None
) -> Reception:
    ref_num = f"REC-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    db_reception = Reception(
        warehouse_id=warehouse_id,
        reference_number=ref_num,
        supplier_name=supplier_name,
        status="DRAFT",
        expected_date=expected_date,
        notes=notes,
    )
    db.add(db_reception)
    await db.flush()
    
    for line in lines_in:
        db_line = ReceptionLine(
            reception_id=db_reception.id,
            product_id=line["product_id"],
            expected_quantity=line["expected_quantity"],
            received_quantity=0.0,
            status="PENDING",
        )
        db.add(db_line)
        
    await db.commit()
    
    # Reload with lines
    res = await db.execute(
        select(Reception)
        .options(selectinload(Reception.lines).selectinload(ReceptionLine.product))
        .filter(Reception.id == db_reception.id)
    )
    return res.scalars().first()

async def update_reception_line(
    db: AsyncSession,
    line_id: str,
    received_quantity: float,
    location_id: str,
    lot_id: Optional[str] = None,
    notes: Optional[str] = None
) -> ReceptionLine:
    res = await db.execute(select(ReceptionLine).filter(ReceptionLine.id == line_id))
    line = res.scalars().first()
    if not line:
        raise HTTPException(status_code=404, detail="Línea de recepción no encontrada")
        
    line.received_quantity = received_quantity
    line.location_id = location_id
    line.lot_id = lot_id
    line.notes = notes
    
    if received_quantity >= line.expected_quantity:
        line.status = "COMPLETE"
    elif received_quantity > 0:
        line.status = "PARTIAL"
    else:
        line.status = "PENDING"
        
    await db.flush()
    return line

async def confirm_reception(
    db: AsyncSession,
    reception_id: str,
    performed_by: str
) -> Reception:
    res = await db.execute(
        select(Reception)
        .options(selectinload(Reception.lines))
        .filter(Reception.id == reception_id)
    )
    reception = res.scalars().first()
    if not reception:
        raise HTTPException(status_code=404, detail="Recepción no encontrada")
    if reception.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="La recepción ya ha sido confirmada")
        
    # Check that all received lines have assigned locations
    for line in reception.lines:
        if line.received_quantity > 0 and not line.location_id:
            raise HTTPException(
                status_code=400,
                detail=f"Debe asignar una ubicación para todos los productos recibidos",
            )
            
    # Process stock entries
    for line in reception.lines:
        if line.received_quantity > 0:
            await add_stock(
                db,
                product_id=line.product_id,
                warehouse_id=reception.warehouse_id,
                location_id=line.location_id,
                quantity=line.received_quantity,
                lot_id=line.lot_id,
                movement_type="ENTRY",
                reference_type="RECEPTION",
                reference_id=reception.id,
                performed_by=performed_by,
                notes=f"Recepción {reception.reference_number}",
            )
            
    reception.status = "COMPLETED"
    reception.received_date = datetime.utcnow()
    reception.received_by = performed_by
    
    await db.commit()
    
    # Reload
    res = await db.execute(
        select(Reception)
        .options(selectinload(Reception.lines).selectinload(ReceptionLine.product))
        .filter(Reception.id == reception.id)
    )
    return res.scalars().first()
