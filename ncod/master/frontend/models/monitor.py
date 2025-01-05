"""Monitor模块"""

import datetime

from database import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship


class DeviceMetric(Base):
    """设备性能指标"""

    __tablename__ = "device_metrics"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    metric_type = Column(String(50))  # cpu, memory, disk, network
    value = Column(JSON)  # 存储指标值和单位
    collected_at = Column(DateTime, default=datetime.datetime.utcnow)

    device = relationship("Device", back_populates="metrics")


class AlertRule(Base):
    """告警规则"""

    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    metric_type = Column(String(50))
    condition = Column(String(10))  # >, >=, <, <=, ==, !=
    threshold = Column(Float)
    severity = Column(String(20))  # critical, high, medium, low
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    alerts = relationship("SystemAlert", back_populates="rule")


class SystemAlert(Base):
    """系统告警"""

    __tablename__ = "system_alerts"

    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))
    title = Column(String(200))
    message = Column(String(500))
    severity = Column(String(20))
    status = Column(String(20), default="active")  # active, resolved
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    rule = relationship("AlertRule", back_populates="alerts")
    device = relationship("Device", back_populates="alerts")
