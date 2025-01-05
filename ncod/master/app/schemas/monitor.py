"""
监控相关的 Pydantic 模型
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class MonitorMetricBase(BaseModel):
    """监控指标基础模型"""

    metric_type: str = Field(..., description="指标类型")
    value: float = Field(..., description="指标值")
    timestamp: datetime = Field(..., description="时间戳")
    group_id: Optional[int] = Field(None, description="组ID")
    user_id: Optional[int] = Field(None, description="用户ID")


class MonitorMetricCreate(MonitorMetricBase):
    """创建监控指标模型"""

    pass


class MonitorMetricResponse(MonitorMetricBase):
    """监控指标响应模型"""

    id: int = Field(..., description="指标ID")

    class Config:
        from_attributes = True


class MonitorAlertBase(BaseModel):
    """监控告警基础模型"""

    alert_type: str = Field(..., description="告警类型")
    message: str = Field(..., description="告警消息")
    value: float = Field(..., description="告警值")
    resolved: bool = Field(False, description="是否已解决")
    group_id: Optional[int] = Field(None, description="组ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外信息")


class MonitorAlertCreate(MonitorAlertBase):
    """创建监控告警模型"""

    pass


class MonitorAlertResponse(MonitorAlertBase):
    """监控告警响应模型"""

    id: int = Field(..., description="告警ID")
    created_at: datetime = Field(..., description="创建时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")

    class Config:
        from_attributes = True


class DeviceUsageBase(BaseModel):
    """设备使用记录基础模型"""

    device_id: int = Field(..., description="设备ID")
    user_id: int = Field(..., description="用户ID")
    group_id: Optional[int] = Field(None, description="组ID")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class DeviceUsageCreate(DeviceUsageBase):
    """创建设备使用记录模型"""

    pass


class DeviceUsageResponse(DeviceUsageBase):
    """设备使用记录响应模型"""

    id: int = Field(..., description="记录ID")

    class Config:
        from_attributes = True
