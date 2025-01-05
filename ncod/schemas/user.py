"""
User schema module
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """用户基础模式"""

    username: str
    email: EmailStr
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    """用户创建模式"""

    password: str


class UserUpdate(BaseModel):
    """用户更新模式"""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """用户数据库模式"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """用户响应模式"""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class UserListResponse(BaseModel):
    """用户列表响应模式"""

    items: List[UserResponse]
    total: int
    page: int
    pages: int
