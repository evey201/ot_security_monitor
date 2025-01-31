from pydantic import BaseModel
from datetime import datetime


class SessionInfo(BaseModel):
    id: int
    device_info: str
    ip_address: str
    created_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True