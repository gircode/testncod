"""User模块"""

import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# 用户-设备关联表
user_device = Table(
    "user_device",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("device_id", Integer, ForeignKey("devices.id")),
)

# 设备组和设备的多对多关联表
device_group_association = Table(
    "device_group_association",
    Base.metadata,
    Column("device_id", Integer, ForeignKey("devices.id")),
    Column("group_id", Integer, ForeignKey("device_groups.id")),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(256), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(20), nullable=False)  # admin, operator, viewer
    permissions = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    password_changed_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    last_login_at = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    lockout_until = Column(DateTime)

    # 关联
    sessions = relationship("Session", back_populates="user")
    password_resets = relationship("PasswordReset", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    devices = relationship("Device", secondary=user_device, back_populates="users")
    tasks = relationship("Task", back_populates="creator")
    notifications = relationship("Notification", back_populates="user")


class DeviceGroup(Base):
    """设备组模型"""

    __tablename__ = "device_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    # 与设备的多对多关系
    devices = relationship(
        "Device", secondary=device_group_association, back_populates="groups"
    )


class Device(Base):
    """设备模型"""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    device_id = Column(String(100), unique=True, nullable=False)
    type = Column(
        String(50), nullable=False
    )  # network, storage, virtualization, container, server
    subtype = Column(String(50))  # router, switch, nas, san, vmware, kvm, docker, k8s
    status = Column(String(20), default="offline")
    ip_address = Column(String(50))
    mac_address = Column(String(17))
    manufacturer = Column(String(100))
    model = Column(String(100))
    os_type = Column(String(50))
    os_version = Column(String(50))
    firmware_version = Column(String(50))
    serial_number = Column(String(100))
    location = Column(String(200))
    config = Column(JSON, default=dict)
    capabilities = Column(JSON, default=list)  # 设备支持的功能列表
    monitoring_config = Column(JSON, default=dict)  # 监控配置
    backup_config = Column(JSON, default=dict)  # 备份配置
    security_config = Column(JSON, default=dict)  # 安全配置
    last_backup = Column(DateTime)
    last_security_scan = Column(DateTime)
    last_heartbeat = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    # 与设备组的多对多关系
    groups = relationship(
        "DeviceGroup", secondary=device_group_association, back_populates="devices"
    )

    # 设备指标关系
    metrics = relationship("DeviceMetric", back_populates="device")

    # 设备任务关系
    tasks = relationship("Task", back_populates="device")

    # 设备告警关系
    alerts = relationship("Alert", back_populates="device")

    # 设备备份关系
    backups = relationship("DeviceBackup", back_populates="device")

    # 设备安全扫描关系
    security_scans = relationship("SecurityScan", back_populates="device")

    # 关联
    users = relationship("User", secondary=user_device, back_populates="devices")


class DeviceBackup(Base):
    """设备备份模型"""

    __tablename__ = "device_backups"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    type = Column(String(50), nullable=False)  # config, full, incremental
    status = Column(String(20), default="pending")
    backup_path = Column(String(500))
    file_size = Column(Integer)
    checksum = Column(String(64))
    retention_days = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)

    device = relationship("Device", back_populates="backups")


class SecurityScan(Base):
    """安全扫描模型"""

    __tablename__ = "security_scans"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    scan_type = Column(String(50), nullable=False)  # vulnerability, compliance, port
    status = Column(String(20), default="pending")
    findings = Column(JSON, default=list)
    risk_level = Column(String(20))  # low, medium, high, critical
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime)

    device = relationship("Device", back_populates="security_scans")


class Alert(Base):
    """告警模型"""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # info, warning, error, critical
    title = Column(String(200), nullable=False)
    message = Column(String(500))
    status = Column(String(20), default="active")  # active, acknowledged, resolved
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    device = relationship("Device", back_populates="alerts")
    acknowledger = relationship("User")


class Task(Base):
    """任务模型"""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    name = Column(String(100))
    type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    device = relationship("Device", back_populates="tasks")
    creator = relationship("User", back_populates="tasks")


class DeviceMetric(Base):
    """设备指标模型"""

    __tablename__ = "device_metrics"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    metric_type = Column(
        String(50), nullable=False
    )  # cpu, memory, disk, network_in, network_out, iops, latency
    metric_name = Column(String(100), nullable=False)
    value = Column(String(100), nullable=False)
    unit = Column(String(20))  # %, MB, GB, Mbps, ms
    tags = Column(JSON, default=dict)
    collected_at = Column(DateTime, default=datetime.datetime.utcnow)

    device = relationship("Device", back_populates="metrics")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(200))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_remembered = Column(Boolean, default=False)

    # 关联
    user = relationship("User", back_populates="sessions")


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)

    # 关联
    user = relationship("User", back_populates="password_resets")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), nullable=False)
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(200))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # 关联
    user = relationship("User", back_populates="audit_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # system, device, task
    title = Column(String(200), nullable=False)
    message = Column(String(500))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # 关联
    user = relationship("User", back_populates="notifications")
