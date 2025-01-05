"""
同步模式
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SyncRequest(BaseModel):
    """同步请求"""

    device_id: UUID
    sync_type: str = Field(..., min_length=1, max_length=50)
    items: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


class SyncResponse(BaseModel):
    """同步响应"""

    record_id: UUID
    status: str
    total_items: int
    processed_items: int
    failed_items: int
    error_message: Optional[str] = None


class SyncRecordBase(BaseModel):
    """同步记录基础模式"""

    device_id: UUID
    sync_type: str = Field(..., min_length=1, max_length=50)
    status: str = Field(..., min_length=1, max_length=20)
    metadata: Optional[Dict[str, Any]] = None


class SyncRecordCreate(SyncRecordBase):
    """同步记录创建模式"""

    start_time: datetime = Field(default_factory=datetime.utcnow)


class SyncRecordInDB(SyncRecordBase):
    """同步记录数据库模式"""

    id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    total_items: int
    processed_items: int
    failed_items: int
    error_message: Optional[str] = None

    class Config:
        orm_mode = True


class SyncItemBase(BaseModel):
    """同步项目基础模式"""

    record_id: UUID
    item_type: str = Field(..., min_length=1, max_length=50)
    item_id: str = Field(..., min_length=1, max_length=100)
    status: str = Field(..., min_length=1, max_length=20)
    metadata: Optional[Dict[str, Any]] = None


class SyncItemCreate(SyncItemBase):
    """同步项目创建模式"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SyncItemInDB(SyncItemBase):
    """同步项目数据库模式"""

    id: UUID
    timestamp: datetime
    error_message: Optional[str] = None

    class Config:
        orm_mode = True
