"""设备监控模型"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, select
from sqlalchemy.orm import relationship
from ncod.core.db.base import BaseModel, TimestampMixin
from ncod.core.logger import setup_logger

logger = setup_logger("monitor_model")


class DeviceMetric(BaseModel, TimestampMixin):
    """设备指标模型"""

    __tablename__ = "device_metrics"

    device_id = Column(String(36), ForeignKey("devices.id"), index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # cpu, memory, disk等
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # %, MB, GB等
    collected_at = Column(DateTime, nullable=False, index=True)

    # 关系
    device = relationship("Device", back_populates="metrics")

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "metric_type": self.metric_type,
            "value": self.value,
            "unit": self.unit,
            "collected_at": self.collected_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    async def get_device_metrics(
        cls,
        session,
        device_id: str,
        metric_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List["DeviceMetric"]:
        """获取设备指标"""
        try:
            stmt = select(cls).where(cls.device_id == device_id)
            if metric_type:
                stmt = stmt.where(cls.metric_type == metric_type)
            if start_time:
                stmt = stmt.where(cls.collected_at >= start_time)
            if end_time:
                stmt = stmt.where(cls.collected_at <= end_time)
            stmt = stmt.order_by(cls.collected_at.desc())
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting device metrics: {e}")
            return []


class DeviceAlert(BaseModel, TimestampMixin):
    """设备告警模型"""

    __tablename__ = "device_alerts"

    device_id = Column(String(36), ForeignKey("devices.id"), index=True)
    alert_type = Column(String(50), nullable=False, index=True)  # offline, high_cpu等
    level = Column(String(20), nullable=False, index=True)  # info, warning, error
    message = Column(String(200), nullable=False)
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)

    # 关系
    device = relationship("Device", back_populates="alerts")

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "alert_type": self.alert_type,
            "level": self.level,
            "message": self.message,
            "is_resolved": self.is_resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    async def get_device_alerts(
        cls,
        session,
        device_id: str,
        alert_type: Optional[str] = None,
        level: Optional[str] = None,
        is_resolved: Optional[bool] = None,
    ) -> List["DeviceAlert"]:
        """获取设备告警"""
        try:
            stmt = select(cls).where(cls.device_id == device_id)
            if alert_type:
                stmt = stmt.where(cls.alert_type == alert_type)
            if level:
                stmt = stmt.where(cls.level == level)
            if is_resolved is not None:
                stmt = stmt.where(cls.is_resolved == is_resolved)
            stmt = stmt.order_by(cls.created_at.desc())
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting device alerts: {e}")
            return []
