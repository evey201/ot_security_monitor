from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db import get_db
from app.models import PowerReadingCreate, PowerReading
from app.services import MonitoringService

router = APIRouter()

@router.post("/readings/", response_model=PowerReading)
async def create_power_reading(
    reading: PowerReadingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new power reading"""
    monitoring_service = MonitoringService(db)
    return await monitoring_service.create_reading(reading)

@router.get("/readings/", response_model=List[PowerReading])
async def get_power_readings(
    skip: int = 0,
    limit: int = 100,
    equipment_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of power readings"""
    monitoring_service = MonitoringService(db)
    return await monitoring_service.get_readings(skip, limit, equipment_id)

@router.get("/readings/{reading_id}", response_model=PowerReading)
async def get_power_reading(
    reading_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific power reading"""
    monitoring_service = MonitoringService(db)
    reading = await monitoring_service.get_reading(reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Reading not found")
    return reading