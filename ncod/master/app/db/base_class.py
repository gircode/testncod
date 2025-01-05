"""
SQLAlchemy 基类模块
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 声明性基类"""

    # 主键ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
