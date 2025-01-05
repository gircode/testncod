"""Device模块"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceBase(BaseModel):
    """Base device model."""

    name: str = Field(..., description="Device name")
    ip_address: str = Field(..., description="Device IP address")
    port: int = Field(..., description="Device port number")
    device_type: str = Field(..., description="Type of device")
    department_id: int = Field(..., description="ID of department owning the device")
    slave_id: int = Field(..., description="ID of slave server managing the device")
    description: Optional[str] = Field(None, description="Device description")


class DeviceCreate(DeviceBase):
    """Device creation model."""

    pass


class DeviceUpdate(BaseModel):
    """Device update model."""

    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    device_type: Optional[str] = None
    department_id: Optional[int] = None
    slave_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Device(DeviceBase):
    """Complete device model."""

    id: int
    status: str = Field(..., description="Current device status")
    last_seen: datetime = Field(..., description="Last time device was seen")
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
