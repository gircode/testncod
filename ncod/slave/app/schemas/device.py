"""
设备模式
"""

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceBase(BaseModel):
    """设备基础模式"""

    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    address: str = Field(..., min_length=1, max_length=200)
    port: str = Field(..., min_length=1, max_length=10)
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceCreate(DeviceBase):
    """设备创建模式"""

    pass


class DeviceUpdate(BaseModel):
    """设备更新模式"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    address: Optional[str] = Field(None, min_length=1, max_length=200)
    port: Optional[str] = Field(None, min_length=1, max_length=10)
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceInDB(DeviceBase):
    """设备数据库模式"""

    id: UUID
    is_connected: bool
    status: str

    class Config:
        orm_mode = True
