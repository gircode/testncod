"""用户模型"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    ForeignKey,
    Table,
    DateTime,
    select,
)
from sqlalchemy.orm import relationship
from ncod.core.db.base import BaseModel, TimestampMixin, SoftDeleteMixin
from ncod.core.logger import setup_logger

logger = setup_logger("user_model")

# 用户-角色关联表
user_roles = Table(
    "user_roles",
    BaseModel.metadata,
    Column("user_id", String(36), ForeignKey("users.id")),
    Column("role_id", String(36), ForeignKey("roles.id")),
)

# 用户-组织关联表
user_organizations = Table(
    "user_organizations",
    BaseModel.metadata,
    Column("user_id", String(36), ForeignKey("users.id")),
    Column("organization_id", String(36), ForeignKey("organizations.id")),
)


class User(BaseModel, TimestampMixin, SoftDeleteMixin):
    """用户模型"""

    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    mac_address = Column(String(17), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)

    # 关系
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    organizations = relationship(
        "Organization", secondary=user_organizations, back_populates="users"
    )
    device_usage = relationship("DeviceUsage", back_populates="user")

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "mac_address": self.mac_address,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "roles": [role.name for role in self.roles],
            "organizations": [org.name for org in self.organizations],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def has_permission(self, permission: str) -> bool:
        """检查权限"""
        return any(permission in role.permissions for role in self.roles)

    def has_role(self, role_name: str) -> bool:
        """检查角色"""
        return any(role.name == role_name for role in self.roles)

    def is_in_organization(self, org_id: str) -> bool:
        """检查组织"""
        return any(org.id == org_id for org in self.organizations)

    async def update_login(self) -> None:
        """更新登录信息"""
        self.last_login = datetime.utcnow()
        self.login_count += 1

    @classmethod
    async def get_by_username(cls, session, username: str) -> Optional["User"]:
        """通过用户名获取用户"""
        try:
            stmt = select(cls).where(cls.username == username)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None

    @classmethod
    async def get_by_email(cls, session, email: str) -> Optional["User"]:
        """通过邮箱获取用户"""
        try:
            stmt = select(cls).where(cls.email == email)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    @classmethod
    async def get_by_mac(cls, session, mac_address: str) -> Optional["User"]:
        """通过MAC地址获取用户"""
        try:
            stmt = select(cls).where(cls.mac_address == mac_address)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by MAC address: {e}")
            return None

    @classmethod
    async def get_active_users(cls, session) -> List["User"]:
        """获取活跃用户"""
        try:
            stmt = select(cls).where(cls.is_active == True)
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
