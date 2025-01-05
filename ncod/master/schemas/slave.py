"""从服务器Schema定义"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from .base import BaseSchema


class SlaveBase(BaseModel):
    """从服务器基础Schema"""

    hostname: str = Field(..., min_length=1, max_length=100)
    ip_address: str = Field(
        ..., pattern=r"^(\d{1,3}\.){3}\d{1,3}$", description="IPv4地址"
    )
    port: int = Field(..., gt=0, lt=65536)
    description: Optional[str] = Field(None, max_length=200)


class SlaveCreate(SlaveBase):
    """从服务器创建Schema"""

    organization_id: str = Field(..., description="组织ID")
    capabilities: Dict[str, Any] = Field(..., description="从服务器能力描述")


class SlaveUpdate(BaseModel):
    """从服务器更新Schema"""

    hostname: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = Field(None, description="从服务器配置")


class SlaveResponse(SlaveBase, BaseSchema):
    """从服务器响应Schema"""

    organization_id: str
    status: str = Field(..., description="从服务器状态")
    last_heartbeat: Optional[datetime] = None
    is_active: bool = True
    device_count: int = Field(0, description="设备数量")
    capabilities: Dict[str, Any] = Field({}, description="从服务器能力")
    config: Dict[str, Any] = Field({}, description="从服务器配置")

    class Config:
        from_attributes = True


class SlaveStatus(BaseModel):
    """从服务器状态Schema"""

    slave_id: str
    status: str = Field(..., description="从服务器状态")
    last_heartbeat: Optional[datetime] = None
    device_count: int = Field(0, description="设备数量")
    cpu_usage: float = Field(0.0, description="CPU使用率")
    memory_usage: float = Field(0.0, description="内存使用率")
    disk_usage: float = Field(0.0, description="磁盘使用率")
    network_io: Dict[str, float] = Field({}, description="网络IO统计")
    device_status: List[Dict[str, Any]] = Field([], description="设备状态列表")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "slave_id": "slave-001",
                "status": "online",
                "last_heartbeat": "2024-01-01T12:00:00",
                "device_count": 5,
                "cpu_usage": 45.2,
                "memory_usage": 62.8,
                "disk_usage": 78.5,
                "network_io": {"bytes_sent": 1024000, "bytes_recv": 2048000},
                "device_status": [
                    {
                        "id": "device-001",
                        "status": "online",
                        "last_seen": "2024-01-01T12:00:00",
                    }
                ],
            }
        }
