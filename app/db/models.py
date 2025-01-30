from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import enum
from datetime import datetime

class Base(DeclarativeBase):
    pass

class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PowerReading(Base):
    __tablename__ = "power_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Power Measurements
    voltage = Column(Float, nullable=False)
    current = Column(Float, nullable=False)
    frequency = Column(Float, nullable=False)
    power_factor = Column(Float)
    
    # Equipment Identifier
    equipment_id = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False)
    
    # Status
    is_anomaly = Column(Boolean, default=False)
    
    # Relationships
    alerts = relationship("Alert", back_populates="power_reading")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Alert Details
    severity = Column(Enum(AlertSeverity), nullable=False)
    message = Column(String, nullable=False)
    description = Column(String)
    
    # Related Reading
    power_reading_id = Column(Integer, ForeignKey("power_readings.id"))
    power_reading = relationship("PowerReading", back_populates="alerts")
    
    # Status
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String)
    acknowledged_at = Column(DateTime(timezone=True))
    
from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLAlchemyEnum
import enum

# Add this to your existing models.py
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
