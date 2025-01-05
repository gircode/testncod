"""设备Schema定义"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from .base import BaseSchema


class DeviceBase(BaseModel):
    """设备基础Schema"""

    name: str = Field(..., min_length=1, max_length=100)
    serial_number: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    vendor: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)


class DeviceCreate(DeviceBase):
    """设备创建Schema"""

    slave_id: str = Field(..., description="从服务器ID")
    organization_id: str = Field(..., description="组织ID")


class DeviceUpdate(BaseModel):
    """设备更新Schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, pattern="^(online|offline|error)$")


class DeviceResponse(DeviceBase, BaseSchema):
    """设备响应Schema"""

    slave_id: str
    organization_id: str
    status: str = Field(..., description="设备状态")
    last_online: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class DeviceUsageLog(BaseSchema):
    """设备使用日志Schema"""

    device_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = Field(..., pattern="^(active|completed|terminated)$")
    notes: Optional[str] = None
