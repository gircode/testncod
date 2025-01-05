"""基础Schema"""

from datetime import datetime
from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """基础Schema类"""

    id: str = Field(..., description="唯一标识符")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Schema配置"""

        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}
