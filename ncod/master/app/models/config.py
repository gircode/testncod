"""
配置模型
"""

from datetime import datetime
from typing import Optional

from app.db.session import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class Config(Base):
    """配置模型"""

    __tablename__ = "configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    group: Mapped[str] = mapped_column(String, nullable=False)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
