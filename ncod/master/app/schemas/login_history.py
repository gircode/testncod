"""
登录历史记录模式
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class LoginHistoryBase(BaseModel):
    """登录历史记录基础模式"""

    success: bool = Field(..., description="是否登录成功")
    ip_address: str = Field(..., description="IP地址")
    user_agent: str = Field(..., description="用户代理")
    error_message: Optional[str] = Field(None, description="错误信息")


class LoginHistoryCreate(LoginHistoryBase):
    """创建登录历史记录模式"""

    user_id: int = Field(..., description="用户ID")


class LoginHistoryResponse(LoginHistoryBase):
    """登录历史记录响应模式"""

    id: int = Field(..., description="记录ID")
    user_id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class LoginHistoryListResponse(BaseModel):
    """登录历史记录列表响应模式"""

    items: List[LoginHistoryResponse] = Field(..., description="记录列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    pages: int = Field(..., description="总页数")
