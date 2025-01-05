"""基础模型"""

from datetime import datetime
from typing import Any
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, DateTime


class Base(DeclarativeBase):
    """基础模型类"""

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    def dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
