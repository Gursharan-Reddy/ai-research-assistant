from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.analytics.metrics import AnalyticsEngine

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    return AnalyticsEngine.get_system_stats(db)