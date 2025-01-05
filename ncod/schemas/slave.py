"""
Slave schema module
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class SlaveBase(BaseModel):
    """从节点基础模式"""

    name: str
    status: str
    description: Optional[str] = None


class SlaveCreate(SlaveBase):
    """从节点创建模式"""

    pass


class SlaveUpdate(BaseModel):
    """从节点更新模式"""

    name: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class SlaveResponse(SlaveBase):
    """从节点响应模式"""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class SlaveListResponse(BaseModel):
    """从节点列表响应模式"""

    items: List[SlaveResponse]
    total: int
    page: int
    pages: int
