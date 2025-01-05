"""通知配置模型"""

from typing import Dict, List, Optional
from sqlalchemy import Column, String, JSON, ForeignKey, select
from sqlalchemy.orm import relationship
from ncod.core.db.base import BaseModel, TimestampMixin
from ncod.core.logger import setup_logger

logger = setup_logger("notify_config")


class NotifyConfig(BaseModel, TimestampMixin):
    """通知配置模型"""

    __tablename__ = "notify_configs"

    name = Column(String(100), nullable=False)
    channel = Column(String(20), nullable=False)  # email, sms, webhook等
    config = Column(JSON, nullable=False)  # 渠道配置
    description = Column(String(200))

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "channel": self.channel,
            "config": self.config,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    async def get_channel_configs(
        cls, session, channel: Optional[str] = None
    ) -> List["NotifyConfig"]:
        """获取通知配置"""
        try:
            stmt = select(cls)
            if channel:
                stmt = stmt.where(cls.channel == channel)
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting notify configs: {e}")
            return []
