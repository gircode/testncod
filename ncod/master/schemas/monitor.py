"""监控Schema定义"""

from typing import Optional, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from ncod.master.schemas.base import BaseSchema


class MetricsBase(BaseModel):
    """指标基础Schema"""

    device_id: str = Field(..., description="设备ID")
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU使用率")
    memory_usage: float = Field(..., ge=0, le=100, description="内存使用率")
    disk_usage: float = Field(..., ge=0, le=100, description="磁盘使用率")
    network_io: Dict[str, int] = Field(..., description="网络IO (rx_bytes, tx_bytes)")
    timestamp: datetime = Field(..., description="时间戳")


class MetricsCreate(MetricsBase):
    """指标创建Schema"""

    pass


class MetricsResponse(MetricsBase, BaseSchema):
    """指标响应Schema"""

    class Config:
        from_attributes = True


class AlertRuleBase(BaseModel):
    """告警规则基础Schema"""

    name: str = Field(..., min_length=1, max_length=100)
    device_id: str = Field(..., description="设备ID")
    metric_type: str = Field(
        ..., description="指标类型", pattern="^(cpu|memory|disk|network)$"
    )
    threshold: float = Field(..., description="阈值")
    operator: str = Field(..., description="操作符", pattern="^(>|<|>=|<=|==)$")
    is_active: bool = Field(default=True, description="是否激活")


class AlertRuleCreate(AlertRuleBase):
    """告警规则创建Schema"""

    pass


class AlertRuleUpdate(BaseModel):
    """告警规则更新Schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    threshold: Optional[float] = None
    operator: Optional[str] = Field(None, pattern="^(>|<|>=|<=|==)$")
    is_active: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase, BaseSchema):
    """告警规则响应Schema"""

    last_triggered: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    """告警基础Schema"""

    rule_id: str = Field(..., description="规则ID")
    device_id: str = Field(..., description="设备ID")
    metric_value: float = Field(..., description="指标值")
    status: str = Field(..., description="状态", pattern="^(active|resolved)$")
    resolved_at: Optional[datetime] = None


class AlertCreate(AlertBase):
    """告警创建Schema"""

    pass


class AlertUpdate(BaseModel):
    """告警更新Schema"""

    status: str = Field(..., description="状态", pattern="^(active|resolved)$")
    resolved_at: Optional[datetime] = None


class AlertResponse(AlertBase, BaseSchema):
    """告警响应Schema"""

    rule: AlertRuleResponse

    class Config:
        from_attributes = True
