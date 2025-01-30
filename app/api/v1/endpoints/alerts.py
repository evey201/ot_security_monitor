from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db import get_db
from app.models import Alert
from app.services.alert import AlertService

router = APIRouter()

@router.get("/alerts/", response_model=List[Alert])
async def get_alerts(
    skip: int = 0,
    limit: int = 100,
    equipment_id: str = None,
    is_acknowledged: bool = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of alerts with optional filtering"""
    alert_service = AlertService(db)
    return await alert_service.get_alerts(
        skip=skip,
        limit=limit,
        equipment_id=equipment_id,
        is_acknowledged=is_acknowledged
    )

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    user_id: str,  # This would come from auth token in real implementation
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an alert"""
    alert_service = AlertService(db)
    try:
        await alert_service.acknowledge_alert(alert_id, user_id)
        return {"message": "Alert acknowledged successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/alerts/summary")
async def get_alert_summary(
    db: AsyncSession = Depends(get_db)
):
    """Get summary of alerts (counts by severity and acknowledgment status)"""
    alert_service = AlertService(db)
    return await alert_service.get_summary()