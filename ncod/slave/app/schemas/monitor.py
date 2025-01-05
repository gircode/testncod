"""
监控指标模式
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MetricBase(BaseModel):
    """指标基础模式"""

    device_id: UUID
    metric_type: str = Field(..., min_length=1, max_length=50)
    value: float
    unit: str = Field(..., min_length=1, max_length=20)
    labels: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class MetricCreate(MetricBase):
    """指标创建模式"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricInDB(MetricBase):
    """指标数据库模式"""

    id: UUID
    timestamp: datetime

    class Config:
        orm_mode = True


class AlertBase(BaseModel):
    """告警基础模式"""

    device_id: UUID
    alert_type: str = Field(..., min_length=1, max_length=50)
    severity: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None


class AlertCreate(AlertBase):
    """告警创建模式"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AlertInDB(AlertBase):
    """告警数据库模式"""

    id: UUID
    status: str
    timestamp: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_note: Optional[str] = None

    class Config:
        orm_mode = True
