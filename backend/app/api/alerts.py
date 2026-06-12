from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.app.database import get_db
from backend.app.core.dependencies import require_viewer, require_operator, get_current_user
from backend.app.models.alert import Alert
from backend.app.models.user import User
from backend.app.schemas.alert import AlertOut
from backend.app.services import alert_service
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[AlertOut], dependencies=[Depends(require_viewer)])
async def list_alerts(
    warehouse_id: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Alert).options(selectinload(Alert.product)).order_by(Alert.created_at.desc())
    if warehouse_id:
        query = query.filter(Alert.warehouse_id == warehouse_id)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)
        
    res = await db.execute(query)
    return res.scalars().all()

@router.post("/check/{warehouse_id}", dependencies=[Depends(require_operator)])
async def trigger_alerts_check(
    warehouse_id: str,
    db: AsyncSession = Depends(get_db)
):
    await alert_service.check_and_generate_alerts(db, warehouse_id)
    return {"message": "Escaneo de inventario completado. Alertas generadas."}

@router.put("/{alert_id}/resolve", response_model=AlertOut, dependencies=[Depends(require_operator)])
async def resolve_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Alert).filter(Alert.id == alert_id))
    alert = res.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
        
    alert.is_resolved = True
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    
    await db.commit()
    
    # Reload
    res = await db.execute(
        select(Alert)
        .options(selectinload(Alert.product))
        .filter(Alert.id == alert_id)
    )
    return res.scalars().first()
