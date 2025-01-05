"""设备使用记录Schema定义"""

from typing import Optional
from datetime import datetime

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field
from ncod.master.schemas.base import BaseSchema


class DeviceUsageBase(BaseModel):
    """设备使用记录基础Schema"""

    device_id: str = Field(..., description="设备ID")
    user_id: str = Field(..., description="用户ID")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    status: str = Field(
        ..., description="使用状态", pattern="^(active|completed|terminated)$"
    )
    connection_info: Optional[str] = Field(None, max_length=200)

    class Config:
        from_attributes = True


class DeviceUsageCreate(BaseModel):
    """设备使用记录创建Schema"""

    device_id: str = Field(..., description="设备ID")
    connection_info: Optional[str] = Field(None, max_length=200)

    class Config:
        from_attributes = True


class DeviceUsageUpdate(BaseModel):
    """设备使用记录更新Schema"""

    end_time: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(active|completed|terminated)$")
    connection_info: Optional[str] = Field(None, max_length=200)

    class Config:
        from_attributes = True


class DeviceUsageResponse(DeviceUsageBase, BaseSchema):
    """设备使用记录响应Schema"""

    class Config:
        from_attributes = True
