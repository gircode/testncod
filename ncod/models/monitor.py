"""监控模型"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime
from pydantic import BaseModel

from ..core.db.base import Base


class SystemMetric(Base):
    """系统指标模型"""

    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_usage = Column(Float)
    disk_free = Column(Integer)
    network_sent = Column(Integer)
    network_recv = Column(Integer)
    connections = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SystemMetricResponse(BaseModel):
    """系统指标响应模型"""

    id: int
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    disk_free: int
    network_sent: int
    network_recv: int
    connections: int
    timestamp: datetime

    class Config:
        from_attributes = True
