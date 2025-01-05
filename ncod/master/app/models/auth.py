"""
认证相关模型
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from app.db.session import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .monitor import DeviceUsage, MonitorAlert, MonitorMetric

# 用户-角色关联表
user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE")),
)

# 角色-权限关联表
role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE")),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE")),
)


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
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    group: Mapped["Group"] = relationship("Group", back_populates="users")
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary=user_role, back_populates="users"
    )
    metrics: Mapped[List["MonitorMetric"]] = relationship(
        "MonitorMetric", back_populates="user"
    )
    alerts: Mapped[List["MonitorAlert"]] = relationship(
        "MonitorAlert", back_populates="user"
    )
    device_usage: Mapped[List["DeviceUsage"]] = relationship(
        "DeviceUsage", back_populates="user"
    )


class Role(Base):
    """角色模型"""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    users: Mapped[List["User"]] = relationship(
        "User", secondary=user_role, back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", secondary=role_permission, back_populates="roles"
    )


class Permission(Base):
    """权限模型"""

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resource: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary=role_permission, back_populates="permissions"
    )


class Group(Base):
    """组模型"""

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    parent: Mapped[Optional["Group"]] = relationship(
        "Group", remote_side=[id], back_populates="children"
    )
    children: Mapped[List["Group"]] = relationship("Group", back_populates="parent")
    users: Mapped[List["User"]] = relationship("User", back_populates="group")
