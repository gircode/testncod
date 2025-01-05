"""角色和权限模型"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship

from ncod.core.db.base import Base

# 角色-权限关联表
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id")),
    Column("permission_id", Integer, ForeignKey("permissions.id")),
)


class Role(Base):
    """角色模型"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    level = Column(Integer, nullable=False)  # 角色级别
    description = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    permissions = relationship("Permission", secondary=role_permissions)
    users = relationship("UserRole", back_populates="role")


class Permission(Base):
    """权限模型"""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)


class UserRole(Base):
    """用户-角色关联"""

    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
