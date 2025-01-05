"""权限Schema定义"""

from typing import Optional, List

try:
    from pydantic.v1 import BaseModel, Field, validator
except ImportError:
    from pydantic import BaseModel, Field, validator
from ncod.master.schemas.base import BaseSchema


class PermissionBase(BaseModel):
    """权限基础Schema"""

    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=200)
    resource_type: str = Field(..., min_length=2, max_length=50)
    action: str = Field(..., min_length=2, max_length=50)

    @classmethod
    @validator("code")
    def validate_code(cls, v: str) -> str:
        """验证权限代码"""
        if not v.isalnum():
            raise ValueError("Code must be alphanumeric")
        return v.upper()


class PermissionCreate(PermissionBase):
    """权限创建Schema"""

    pass


class PermissionUpdate(BaseModel):
    """权限更新Schema"""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class PermissionResponse(PermissionBase, BaseSchema):
    """权限响应Schema"""

    is_active: bool

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """角色基础Schema"""

    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=200)
    organization_id: str

    @classmethod
    @validator("code")
    def validate_code(cls, v: str) -> str:
        """验证角色代码"""
        if not v.isalnum():
            raise ValueError("Code must be alphanumeric")
        return v.upper()


class RoleCreate(RoleBase):
    """角色创建Schema"""

    permission_ids: List[str] = Field([], description="权限ID列表")


class RoleUpdate(BaseModel):
    """角色更新Schema"""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    permission_ids: Optional[List[str]] = None


class RoleResponse(RoleBase, BaseSchema):
    """角色响应Schema"""

    is_active: bool
    permissions: List[PermissionResponse] = []

    class Config:
        from_attributes = True
