"""告警规则模型"""

from typing import Dict, List, Optional
from sqlalchemy import Column, String, Float, Boolean, JSON, ForeignKey, select
from sqlalchemy.orm import relationship
from ncod.core.db.base import BaseModel, TimestampMixin
from ncod.core.logger import setup_logger

logger = setup_logger("alert_rule")


class AlertRule(BaseModel, TimestampMixin):
    """告警规则模型"""

    __tablename__ = "alert_rules"

    name = Column(String(100), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), index=True)
    metric_type = Column(String(50), nullable=False)
    condition = Column(String(20), nullable=False)  # gt, lt, eq等
    threshold = Column(Float, nullable=False)
    level = Column(String(20), nullable=False)  # critical, major, minor, info
    enabled = Column(Boolean, default=True)
    notify_channels = Column(JSON)  # 通知渠道配置
    description = Column(String(200))

    # 关系
    device = relationship("Device", back_populates="alert_rules")

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "device_id": self.device_id,
            "metric_type": self.metric_type,
            "condition": self.condition,
            "threshold": self.threshold,
            "level": self.level,
            "enabled": self.enabled,
            "notify_channels": self.notify_channels,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    async def get_device_rules(
        cls, session, device_id: str, enabled: Optional[bool] = None
    ) -> List["AlertRule"]:
        """获取设备告警规则"""
        try:
            stmt = select(cls).where(cls.device_id == device_id)
            if enabled is not None:
                stmt = stmt.where(cls.enabled == enabled)
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting device alert rules: {e}")
            return []
