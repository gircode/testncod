"""数据库基础模块"""

from datetime import datetime
import uuid
from typing import Any, Dict
from sqlalchemy import MetaData, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr

# 命名约定
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# 创建元数据
metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """基础模型类"""

    metadata = metadata

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """获取表名"""
        return cls.__name__.lower()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        """从字典创建实例"""
        return cls(
            **{k: v for k, v in data.items() if k in inspect(cls).mapper.column_attrs}
        )


class TimestampMixin:
    """时间戳混入类"""

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True
    )


class UUIDMixin:
    """UUID混入类"""

    id: Mapped[str] = mapped_column(
        primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )


class SoftDeleteMixin:
    """软删除混入类"""

    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
    deleted_at: Mapped[datetime] = mapped_column(nullable=True, index=True)

    def soft_delete(self) -> None:
        """软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """基础模型"""

    __abstract__ = True

    def update(self, data: Dict[str, Any]) -> None:
        """更新模型"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
