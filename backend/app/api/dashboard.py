from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_db
from backend.app.core.dependencies import require_viewer
from backend.app.services import kpi_service, ai_service
from pydantic import BaseModel

router = APIRouter()

class NLPQueryRequest(BaseModel):
    warehouse_id: str
    query_text: str

@router.get("/summary/{warehouse_id}", dependencies=[Depends(require_viewer)])
async def get_dashboard_summary_endpoint(
    warehouse_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await kpi_service.get_dashboard_summary(db, warehouse_id)

@router.post("/nlp-assistant", dependencies=[Depends(require_viewer)])
async def nlp_assistant_endpoint(
    req: NLPQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    answer = await ai_service.process_nlp_assistant_query(db, req.warehouse_id, req.query_text)
    return {"response": answer}
