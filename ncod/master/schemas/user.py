"""用户Schema定义"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
from ncod.master.schemas.base import BaseSchema
from ncod.master.schemas.permission import RoleResponse


class UserBase(BaseModel):
    """用户基础Schema"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., description="电子邮件")
    full_name: Optional[str] = Field(None, max_length=100)
    organization_id: str = Field(..., description="组织ID")

    @validator("username")
    def username_alphanumeric(cls, v):
        """验证用户名"""
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v


class UserCreate(UserBase):
    """用户创建Schema"""

    password: str = Field(..., min_length=8, max_length=64)


class UserUpdate(BaseModel):
    """用户更新Schema"""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=64)
    is_active: Optional[bool] = None


class UserResponse(UserBase, BaseSchema):
    """用户响应Schema"""

    is_active: bool
    last_login: Optional[datetime] = None
    roles: List[RoleResponse] = []

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    """数据库中的用户Schema"""

    hashed_password: str

    class Config:
        from_attributes = True
