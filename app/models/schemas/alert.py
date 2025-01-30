from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.db.models import AlertSeverity

class AlertBase(BaseModel):
    severity: AlertSeverity
    message: str = Field(..., min_length=1)
    description: Optional[str] = None
    power_reading_id: int

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    id: int
    timestamp: datetime
    is_acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    class Config:
        from_attributes = True