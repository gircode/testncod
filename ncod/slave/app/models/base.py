"""
基础模型
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    """基础模型类"""

    id: Any
    __name__: str

    # 生成表名
    @declared_attr
    def __tablename__(cls) -> str:
        """生成表名"""
        return cls.__name__.lower()

    # 通用字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
