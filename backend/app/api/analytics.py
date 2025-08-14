from fastapi import APIRouter, Query
from app.services.analytics import summary
router = APIRouter()
@router.get("/summary")
async def get_summary(days: int = Query(7, ge=1, le=90)):
    return await summary(days)
