from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PowerReadingBase(BaseModel):
    voltage: float = Field(..., description="Voltage reading in volts", ge=0)
    current: float = Field(..., description="Current reading in amperes", ge=0)
    frequency: float = Field(..., description="Frequency in Hz", ge=0)
    power_factor: Optional[float] = Field(None, description="Power factor", ge=-1, le=1)
    equipment_id: str = Field(..., description="Unique identifier for the equipment")
    location: str = Field(..., description="Location of the equipment")

class PowerReadingCreate(PowerReadingBase):
    pass

class PowerReading(PowerReadingBase):
    id: int
    timestamp: datetime
    is_anomaly: bool

    class Config:
        from_attributes = True