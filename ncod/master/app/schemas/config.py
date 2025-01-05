"""
配置相关的 Pydantic 模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ConfigBase(BaseModel):
    """配置基础模型"""

    key: str = Field(..., description="配置键")
    value: str = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    group: str = Field(..., description="配置组")
    is_secret: bool = Field(False, description="是否为敏感配置")


class ConfigCreate(ConfigBase):
    """创建配置模型"""

    pass


class ConfigUpdate(BaseModel):
    """更新配置模型"""

    value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    group: Optional[str] = Field(None, description="配置组")
    is_secret: Optional[bool] = Field(None, description="是否为敏感配置")


class ConfigResponse(ConfigBase):
    """配置响应模型"""

    id: int = Field(..., description="配置ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ConfigSearch(BaseModel):
    """配置搜索模型"""

    key: Optional[str] = Field(None, description="配置键")
    group: Optional[str] = Field(None, description="配置组")
    is_secret: Optional[bool] = Field(None, description="是否为敏感配置")
