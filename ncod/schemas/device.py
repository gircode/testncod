"""设备相关模型"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class DevicePortBase(BaseModel):
    """设备端口基础模型"""

    port_number: int = Field(..., ge=1)
    port_type: str = Field(..., min_length=1, max_length=20)
    is_enabled: bool = True


class DevicePortCreate(DevicePortBase):
    """设备端口创建模型"""

    device_id: int


class DevicePortUpdate(BaseModel):
    """设备端口更新模型"""

    is_enabled: bool | None = None
    is_occupied: bool | None = None


class DevicePortInDB(DevicePortBase):
    """数据库中的设备端口模型"""

    id: int
    device_id: int
    is_occupied: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DevicePort(DevicePortInDB):
    """设备端口API模型"""

    pass


class DeviceStats(BaseModel):
    """设备状态模型"""

    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: dict
    uptime: int
    timestamp: datetime


class DeviceStatus(BaseModel):
    """设备状态响应模型"""

    is_online: bool
    last_online: datetime | None
    stats: DeviceStats | None = None
