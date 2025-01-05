"""组织架构Schema"""

from typing import Optional
from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    """组织基础模型"""

    name: str = Field(..., description="组织名称")
    code: str = Field(..., description="组织代码")
    description: Optional[str] = Field(None, description="组织描述")
    parent_id: Optional[int] = Field(None, description="父组织ID")


class OrganizationCreate(OrganizationBase):
    """创建组织模型"""

    pass


class OrganizationUpdate(BaseModel):
    """更新组织模型"""

    name: Optional[str] = Field(None, description="组织名称")
    code: Optional[str] = Field(None, description="组织代码")
    description: Optional[str] = Field(None, description="组织描述")
    parent_id: Optional[int] = Field(None, description="父组织ID")
    is_active: Optional[bool] = Field(None, description="是否激活")


class OrganizationInDB(OrganizationBase):
    """数据库中的组织模型"""

    id: int = Field(..., description="组织ID")
    is_active: bool = Field(True, description="是否激活")
    level: int = Field(..., description="组织层级")
    path: str = Field(..., description="组织路径")

    class Config:
        """配置"""

        from_attributes = True
