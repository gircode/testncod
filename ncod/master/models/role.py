"""角色模型"""

from typing import Dict, List, Optional
from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from ncod.core.db.base import BaseModel, TimestampMixin
from ncod.core.logger import setup_logger

logger = setup_logger("role_model")

# 角色-权限关联表
role_permissions = Table(
    "role_permissions",
    BaseModel.metadata,
    Column("role_id", String(36), ForeignKey("roles.id")),
    Column("permission_id", String(36), ForeignKey("permissions.id")),
)


class Role(BaseModel, TimestampMixin):
    """角色模型"""

    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200))
    is_system = Column(Boolean, default=False)  # 系统角色标记

    # 关系
    users = relationship("User", secondary="user_roles", back_populates="roles")
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_system": self.is_system,
            "permissions": [p.code for p in self.permissions],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    async def get_by_name(cls, session, name: str) -> Optional["Role"]:
        """通过名称获取角色"""
        try:
            stmt = select(cls).where(cls.name == name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting role by name: {e}")
            return None

    @classmethod
    async def get_system_roles(cls, session) -> List["Role"]:
        """获取系统角色"""
        try:
            stmt = select(cls).where(cls.is_system == True)
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting system roles: {e}")
            return []
