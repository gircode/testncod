"""设备使用记录模型"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ncod.core.db.database import Base
from ncod.master.models.base import BaseModel


class DeviceUsage(Base, BaseModel):
    """设备使用记录模型"""

    __tablename__ = "device_usage"

    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(
        String(20), nullable=False, default="active"
    )  # active, completed, terminated
    connection_info = Column(String(200))

    # 关系
    device = relationship("Device", back_populates="usage_logs")
    user = relationship("User", back_populates="device_usage")

    def __repr__(self) -> str:
        return (
            f"<DeviceUsage device={self.device_id} "
            f"user={self.user_id} status={self.status}>"
        )
