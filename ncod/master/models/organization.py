"""组织模型"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ncod.master.core.base import BaseModel, TimestampMixin
import logging

logger = logging.getLogger("organization_model")


class Organization(BaseModel, TimestampMixin):
    """组织模型"""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200))
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("organizations.id")
    )
    level: Mapped[int] = mapped_column(Integer, default=0)
    path: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 关系
    parent = relationship("Organization", remote_side=[id], back_populates="children")
    children = relationship("Organization", back_populates="parent")
    users = relationship(
        "User", secondary="user_organizations", back_populates="organizations"
    )

    @classmethod
    async def get_root_organizations(cls, session) -> List["Organization"]:
        """获取根组织"""
        try:
            stmt = select(cls).where(cls.parent_id.is_(None))
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting root organizations: {e}")
            return []


class AuditLog(BaseModel, TimestampMixin):
    """审计日志模型"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50))
    resource_id: Mapped[Optional[str]] = mapped_column(String(50))
    details: Mapped[Optional[str]] = mapped_column(String(500))
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
