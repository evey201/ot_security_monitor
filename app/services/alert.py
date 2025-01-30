from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import List, Optional, Dict
from app.db import Alert as AlertModel, AlertSeverity

class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_alerts(
        self,
        skip: int = 0,
        limit: int = 100,
        equipment_id: Optional[str] = None,
        is_acknowledged: Optional[bool] = None
    ) -> List[AlertModel]:
        """Get filtered list of alerts"""
        query = select(AlertModel)

        # Apply filters if provided
        if equipment_id:
            query = query.join(AlertModel.power_reading).filter(
                AlertModel.power_reading.has(equipment_id=equipment_id)
            )
        if is_acknowledged is not None:
            query = query.filter(AlertModel.is_acknowledged == is_acknowledged)

        # Order by timestamp descending (newest first)
        query = query.order_by(AlertModel.timestamp.desc())
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def acknowledge_alert(self, alert_id: int, user_id: str):
        """Mark an alert as acknowledged"""
        query = select(AlertModel).filter(AlertModel.id == alert_id)
        result = await self.db.execute(query)
        alert = result.scalar_one_or_none()

        if not alert:
            raise ValueError(f"Alert with id {alert_id} not found")

        if alert.is_acknowledged:
            raise ValueError(f"Alert already acknowledged by {alert.acknowledged_by}")

        alert.is_acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()

        await self.db.commit()

    async def get_summary(self) -> Dict:
        """Get summary of alerts"""
        # Count alerts by severity
        severity_query = select(
            AlertModel.severity,
            func.count(AlertModel.id)
        ).group_by(AlertModel.severity)

        # Count unacknowledged alerts
        unacknowledged_query = select(func.count(AlertModel.id)).filter(
            AlertModel.is_acknowledged == False  # noqa: E712
        )

        severity_result = await self.db.execute(severity_query)
        unacknowledged_result = await self.db.execute(unacknowledged_query)

        severity_counts = {
            severity.name: count 
            for severity, count in severity_result.all()
        }
        unacknowledged_count = unacknowledged_result.scalar()

        return {
            "total_alerts": sum(severity_counts.values()),
            "by_severity": severity_counts,
            "unacknowledged": unacknowledged_count
        }