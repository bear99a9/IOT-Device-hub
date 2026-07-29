from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, Literal, List
from datetime import datetime



class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1, examples=["Living Room Thermometer"])
    type: str = Field(..., min_length=1, examples=["thermometer"])
    config: Optional[Dict[str, Any]] = Field(
        default=None, examples=[{"target_temperature": 21}]
    )

class DeviceCreate(DeviceBase):
    status: Optional[Literal["on", "off"]] = Field(
        default="off", examples=["on", "off"]
    )

class DeviceOut(DeviceBase):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, examples=["on"])

class HistoryEntry(BaseModel):
    status: str
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DeviceWithHistory(DeviceOut):
    history: List[HistoryEntry] = []