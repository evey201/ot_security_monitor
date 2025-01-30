from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db import PowerReading as PowerReadingModel, Alert as AlertModel, AlertSeverity
from app.models import PowerReadingCreate
from app.core.config import get_settings

settings = get_settings()

class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reading(self, reading: PowerReadingCreate) -> PowerReadingModel:
        """Create a new power reading and check for anomalies"""
        # Create new reading
        db_reading = PowerReadingModel(
            voltage=reading.voltage,
            current=reading.current,
            frequency=reading.frequency,
            power_factor=reading.power_factor,
            equipment_id=reading.equipment_id,
            location=reading.location
        )
        
        # Check for anomalies and set flag
        is_anomaly = self._check_anomalies(db_reading)
        db_reading.is_anomaly = is_anomaly
        
        # Add to database
        self.db.add(db_reading)
        await self.db.flush()
        
        # Generate alert if anomaly detected
        if is_anomaly:
            await self._generate_alert(db_reading)
        
        await self.db.commit()
        return db_reading

    # basically this is a safety checker
    def _check_anomalies(self, reading: PowerReadingModel) -> bool:
        """Check for anomalies in power readings"""
        # Voltage check
        if abs(reading.voltage - settings.ALERT_THRESHOLD_VOLTAGE) > 10:
            return True
        
        # Current check
        if reading.current > settings.ALERT_THRESHOLD_CURRENT:
            return True
        
        # Frequency check (standard 50/60 Hz)
        if not (45 <= reading.frequency <= 65):
            return True
        
        return False

    async def _generate_alert(self, reading: PowerReadingModel):
        """Generate alert for anomalous reading"""
        severity = self._determine_severity(reading)
        
        alert = AlertModel(
            severity=severity,
            message=f"Anomaly detected in {reading.equipment_id}",
            description=self._generate_alert_description(reading),
            power_reading_id=reading.id
        )
        
        self.db.add(alert)

    def _determine_severity(self, reading: PowerReadingModel) -> AlertSeverity:
        """Determine alert severity based on reading values"""
        # Voltage deviation percentage
        voltage_dev = abs(reading.voltage - settings.ALERT_THRESHOLD_VOLTAGE) / settings.ALERT_THRESHOLD_VOLTAGE * 100
        
        if voltage_dev > 20 or reading.current > settings.ALERT_THRESHOLD_CURRENT * 1.5:
            return AlertSeverity.CRITICAL
        elif voltage_dev > 15 or reading.current > settings.ALERT_THRESHOLD_CURRENT * 1.2:
            return AlertSeverity.HIGH
        elif voltage_dev > 10 or reading.current > settings.ALERT_THRESHOLD_CURRENT:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW

    def _generate_alert_description(self, reading: PowerReadingModel) -> str:
        """Generate detailed alert description"""
        issues = []
        
        if abs(reading.voltage - settings.ALERT_THRESHOLD_VOLTAGE) > 10:
            issues.append(f"Voltage deviation: {reading.voltage}V")
        if reading.current > settings.ALERT_THRESHOLD_CURRENT:
            issues.append(f"High current: {reading.current}A")
        if not (45 <= reading.frequency <= 65):
            issues.append(f"Frequency issue: {reading.frequency}Hz")
            
        return "Issues detected: " + "; ".join(issues)

    async def get_readings(
        self, 
        skip: int = 0, 
        limit: int = 100,
        equipment_id: Optional[str] = None
    ) -> List[PowerReadingModel]:
        """Get list of power readings"""
        query = select(PowerReadingModel)
        
        if equipment_id:
            query = query.where(PowerReadingModel.equipment_id == equipment_id)
            
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_reading(self, reading_id: int) -> Optional[PowerReadingModel]:
        """Get a specific power reading"""
        query = select(PowerReadingModel).where(PowerReadingModel.id == reading_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()