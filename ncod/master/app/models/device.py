"""
设备相关模型
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from app.db.session import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .auth import Group, User
    from .monitor import DeviceUsage


class Device(Base):
    """设备模型"""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    virtualhere_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String, default="available")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"))
    slave_server_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("slave_servers.id")
    )
    current_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 关系
    group: Mapped[Optional["Group"]] = relationship("Group")
    slave_server: Mapped[Optional["SlaveServer"]] = relationship(
        "SlaveServer", back_populates="devices"
    )
    current_user: Mapped[Optional["User"]] = relationship("User")
    usage_records: Mapped[List["DeviceUsage"]] = relationship(
        "DeviceUsage", back_populates="device"
    )
    permissions: Mapped[List["DevicePermission"]] = relationship(
        "DevicePermission", back_populates="device"
    )
    reservations: Mapped[List["DeviceReservation"]] = relationship(
        "DeviceReservation", back_populates="device"
    )


class DevicePermission(Base):
    """设备权限模型"""

    __tablename__ = "device_permissions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    granted_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    permission_type: Mapped[str] = mapped_column(String, default="read")
    is_temporary: Mapped[bool] = mapped_column(Boolean, default=False)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    device: Mapped["Device"] = relationship("Device", back_populates="permissions")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    granted_by: Mapped["User"] = relationship("User", foreign_keys=[granted_by_id])


class DeviceReservation(Base):
    """设备预约模型"""

    __tablename__ = "device_reservations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="pending")
    remarks: Mapped[Optional[str]] = mapped_column(String)
    handled_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    device: Mapped["Device"] = relationship("Device", back_populates="reservations")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    handled_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[handled_by_id]
    )


class SlaveServer(Base):
    """从服务器模型"""

    __tablename__ = "slave_servers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    host: Mapped[str] = mapped_column(String, nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 关系
    devices: Mapped[List["Device"]] = relationship(
        "Device", back_populates="slave_server"
    )


class GroupRelation(Base):
    """组间关系模型"""

    __tablename__ = "group_relations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    related_group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    allow_device_sharing: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    group: Mapped["Group"] = relationship("Group", foreign_keys=[group_id])
    related_group: Mapped["Group"] = relationship(
        "Group", foreign_keys=[related_group_id]
    )
