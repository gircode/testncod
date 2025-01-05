"""权限模型"""

from typing import Dict, List, Optional
from sqlalchemy import Column, String, select
from sqlalchemy.orm import relationship
from ncod.core.db.base import BaseModel, TimestampMixin
from ncod.core.logger import setup_logger

logger = setup_logger("permission_model")


class Permission(BaseModel, TimestampMixin):
    """权限模型"""

    __tablename__ = "permissions"

    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(200))
    module = Column(String(50), nullable=False, index=True)  # 功能模块

    # 关系
    roles = relationship(
        "Role", secondary="role_permissions", back_populates="permissions"
    )

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "module": self.module,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    async def get_by_code(cls, session, code: str) -> Optional["Permission"]:
        """通过代码获取权限"""
        try:
            stmt = select(cls).where(cls.code == code)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting permission by code: {e}")
            return None

    @classmethod
    async def get_by_module(cls, session, module: str) -> List["Permission"]:
        """获取模块权限"""
        try:
            stmt = select(cls).where(cls.module == module)
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting permissions by module: {e}")
            return []
