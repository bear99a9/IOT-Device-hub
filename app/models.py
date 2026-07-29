import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  #  example: "thermostat"
    status = Column(String, nullable=False, default="off")
    config = Column(JSON, nullable=True) # example: {"target_temperature": 21}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    history = relationship(
        "StatusHistory",
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="StatusHistory.changed_at",
    )

class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(String, primary_key=True, default=generate_uuid)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    status = Column(String, nullable=False)
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    device = relationship("Device", back_populates="history")
