"""
用户模型
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from app.db.session import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.config import SystemConfig


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    configs: Mapped[List["SystemConfig"]] = relationship(
        "SystemConfig", back_populates="creator", foreign_keys="SystemConfig.created_by"
    )
    updated_configs: Mapped[List["SystemConfig"]] = relationship(
        "SystemConfig", back_populates="updater", foreign_keys="SystemConfig.updated_by"
    )
