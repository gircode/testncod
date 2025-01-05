"""数据库模型"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text as sql_text

from ..db.base_class import Base as DBBase


class ConfigVersion(DBBase):
    """配置版本模型"""

    __tablename__ = "config_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_data: Mapped[Dict[str, Any]] = mapped_column(JSON)
    version: Mapped[str] = mapped_column(String, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sql_text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=sql_text("CURRENT_TIMESTAMP"),
        server_default=sql_text("CURRENT_TIMESTAMP"),
    )

    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    creator: Mapped["User"] = relationship(back_populates="config_versions")


class User(DBBase):
    """用户模型"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sql_text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=sql_text("CURRENT_TIMESTAMP"),
        server_default=sql_text("CURRENT_TIMESTAMP"),
    )

    # 关系
    devices: Mapped[List["Device"]] = relationship(back_populates="owner")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")
    config_versions: Mapped[List["ConfigVersion"]] = relationship(
        back_populates="creator"
    )
    device_permissions: Mapped[List["DevicePermission"]] = relationship(
        back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Device(DBBase):
    """设备模型"""

    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    device_type: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON)
    last_online: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sql_text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=sql_text("CURRENT_TIMESTAMP"),
        server_default=sql_text("CURRENT_TIMESTAMP"),
    )

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    slave_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("slaves.id"), nullable=True
    )

    owner: Mapped["User"] = relationship(back_populates="devices")
    slave: Mapped["Slave"] = relationship(back_populates="devices")
    metrics: Mapped[List["DeviceMetric"]] = relationship(back_populates="device")
    permissions: Mapped[List["DevicePermission"]] = relationship(
        back_populates="device"
    )


class DevicePermission(DBBase):
    """设备权限模型"""

    __tablename__ = "device_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"))
    action: Mapped[str] = mapped_column(String, index=True)  # read, write, admin
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sql_text("CURRENT_TIMESTAMP")
    )

    user: Mapped["User"] = relationship(back_populates="device_permissions")
    device: Mapped["Device"] = relationship(back_populates="permissions")


class DeviceMetric(DBBase):
    """设备指标模型"""

    __tablename__ = "device_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String, ForeignKey("devices.id"))
    metric_type: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sql_text("CURRENT_TIMESTAMP")
    )

    device: Mapped["Device"] = relationship(back_populates="metrics")


class Slave(DBBase):
    """从服务器模型"""

    __tablename__ = "slaves"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    auth_token: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, index=True)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    config: Mapped[Dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sql_text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=sql_text("CURRENT_TIMESTAMP"),
        server_default=sql_text("CURRENT_TIMESTAMP"),
    )

    devices: Mapped[List["Device"]] = relationship(back_populates="slave")
    metrics: Mapped[List["SlaveMetric"]] = relationship(back_populates="slave")


class SlaveMetric(DBBase):
    """从服务器指标模型"""

    __tablename__ = "slave_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slave_id: Mapped[str] = mapped_column(String, ForeignKey("slaves.id"))
    metric_type: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sql_text("CURRENT_TIMESTAMP")
    )

    slave: Mapped["Slave"] = relationship(back_populates="metrics")


class AuditLog(DBBase):
    """审计日志模型"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String, index=True)
    resource_type: Mapped[str] = mapped_column(String, index=True)
    resource_id: Mapped[str] = mapped_column(String, index=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sql_text("CURRENT_TIMESTAMP")
    )

    user: Mapped["User"] = relationship()


class SystemConfig(DBBase):
    """系统配置模型"""

    __tablename__ = "system_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String, unique=True, index=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSON)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sql_text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=sql_text("CURRENT_TIMESTAMP"),
        server_default=sql_text("CURRENT_TIMESTAMP"),
    )
