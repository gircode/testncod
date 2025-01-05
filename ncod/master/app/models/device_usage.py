"""
设备使用记录模型
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.db.session import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .auth import Group, User


class DeviceUsage(Base):
    """设备使用记录模型"""

    __tablename__ = "device_usage"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="device_usage")
    group: Mapped[Optional["Group"]] = relationship("Group")
