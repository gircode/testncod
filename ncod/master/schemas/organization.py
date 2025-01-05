"""组织Schema定义"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from ncod.master.schemas.base import BaseSchema


class OrganizationBase(BaseModel):
    """组织基础Schema"""

    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    parent_id: Optional[str] = None

    @validator("code")
    def validate_code(cls, v: str) -> str:
        """验证组织代码"""
        if not v.isalnum():
            raise ValueError("Code must be alphanumeric")
        return v.upper()


class OrganizationCreate(OrganizationBase):
    """组织创建Schema"""

    pass


class OrganizationUpdate(BaseModel):
    """组织更新Schema"""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase, BaseSchema):
    """组织响应Schema"""

    is_active: bool
    level: int
    user_count: int = Field(0, description="用户数量")
    device_count: int = Field(0, description="设备数量")
    slave_count: int = Field(0, description="从服务器数量")

    class Config:
        from_attributes = True


class OrganizationTree(OrganizationResponse):
    """组织树Schema"""

    children: List["OrganizationTree"] = []

    class Config:
        from_attributes = True
