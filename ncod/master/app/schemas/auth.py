"""
认证相关的数据模式
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


class Token(BaseModel):
    """访问令牌"""

    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """令牌载荷"""

    sub: Optional[str] = None
    exp: Optional[datetime] = None


class UserBase(BaseModel):
    """用户基础模式"""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """创建用户"""

    password: str = Field(..., min_length=6, max_length=32)

    @validator("password")
    def validate_password(cls, v):
        """验证密码强度"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class UserUpdate(BaseModel):
    """更新用户"""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=6, max_length=32)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

    @validator("password")
    def validate_password(cls, v):
        """验证密码强度"""
        if v is None:
            return v
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class UserInDBBase(UserBase):
    """数据库中的用户基础模式"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(UserInDBBase):
    """用户响应模式"""

    roles: List["RoleResponse"] = []


class UserListResponse(BaseModel):
    """用户列表响应"""

    items: List[UserResponse]
    total: int
    page: int
    pages: int


class RoleBase(BaseModel):
    """角色基础模式"""

    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class RoleCreate(RoleBase):
    """创建角色"""

    pass


class RoleUpdate(BaseModel):
    """更新角色"""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class RoleInDBBase(RoleBase):
    """数据库中的角色基础模式"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleResponse(RoleInDBBase):
    """角色响应模式"""

    permissions: List["PermissionResponse"] = []


class PermissionBase(BaseModel):
    """权限基础模式"""

    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class PermissionCreate(PermissionBase):
    """创建权限"""

    pass


class PermissionUpdate(BaseModel):
    """更新权限"""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class PermissionInDBBase(PermissionBase):
    """数据库中的权限基础模式"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PermissionResponse(PermissionInDBBase):
    """权限响应模式"""

    pass


# 更新引用
UserResponse.model_rebuild()
RoleResponse.model_rebuild()
