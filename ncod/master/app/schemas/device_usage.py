"""Device Usage模块"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceUsageRecordBase(BaseModel):
    """Base device usage record model."""

    device_id: int = Field(..., description="ID of the device")
    user_id: int = Field(..., description="ID of the user")
    notes: Optional[str] = Field(None, description="Usage notes")


class DeviceUsageRecordCreate(DeviceUsageRecordBase):
    """Device usage record creation model."""

    pass


class DeviceUsageRecordUpdate(BaseModel):
    """Device usage record update model."""

    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class DeviceUsageRecord(DeviceUsageRecordBase):
    """Complete device usage record model."""

    id: int
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    status: str

    class Config:
        from_attributes = True


class DeviceUsageRecordWithDetails(DeviceUsageRecord):
    """Device usage record model with related details."""

    device_name: str = Field(..., description="Name of the device")
    user_name: str = Field(..., description="Name of the user")

    class Config:
        from_attributes = True
