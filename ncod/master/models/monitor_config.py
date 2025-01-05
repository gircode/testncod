"""监控配置模型"""

from typing import Dict, List, Optional
from sqlalchemy import Column, String, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ncod.core.db.base import BaseModel, TimestampMixin
from ncod.core.logger import setup_logger

logger = setup_logger("monitor_config")


class MonitorConfig(BaseModel, TimestampMixin):
    """监控配置模型"""

    __tablename__ = "monitor_configs"

    device_id = Column(String(36), ForeignKey("devices.id"), index=True)
    metric_type = Column(String(50), nullable=False)  # cpu, memory, disk等
    enabled = Column(Boolean, default=True)
    threshold = Column(Float)  # 阈值
    interval = Column(Integer, default=30)  # 采集间隔(秒)
    alert_levels = Column(JSON)  # 告警级别配置
    description = Column(String(200))

    # 关系
    device = relationship("Device", back_populates="monitor_configs")

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "metric_type": self.metric_type,
            "enabled": self.enabled,
            "threshold": self.threshold,
            "interval": self.interval,
            "alert_levels": self.alert_levels,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    async def get_device_configs(cls, session, device_id: str) -> List["MonitorConfig"]:
        """获取设备监控配置"""
        try:
            stmt = select(cls).where(cls.device_id == device_id)
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting device configs: {e}")
            return []
