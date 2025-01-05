"""监控指标模型"""

from datetime import datetime
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ncod.core.db.database import Base
from ncod.master.models.base import BaseModel


class Metrics(Base, BaseModel):
    __tablename__ = "metrics"

    slave_id = Column(String(36), ForeignKey("slaves.id"), nullable=False)
    metrics_data = Column(JSON, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 关系
    slave = relationship("Slave", back_populates="metrics")


class Alert(Base, BaseModel):
    __tablename__ = "alerts"

    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    slave_id = Column(String(36), ForeignKey("slaves.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    message = Column(String(255), nullable=False)
    metrics_data = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default="active")

    # 关系
    organization = relationship("Organization", back_populates="alerts")
    slave = relationship("Slave", back_populates="alerts")
