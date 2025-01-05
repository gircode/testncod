"""Rbac模块"""

import datetime

from database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

# 角色-权限关联表
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id")),
    Column("permission_id", Integer, ForeignKey("permissions.id")),
)

# 用户-角色关联表
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("role_id", Integer, ForeignKey("roles.id")),
)


class Role(Base):
    """角色"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )
    users = relationship("User", secondary=user_roles, back_populates="roles")


class Permission(Base):
    """权限"""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    code = Column(String(50), unique=True)  # 权限代码,如: device:view, task:create
    description = Column(String(200))
    resource_type = Column(String(50))  # 资源类型: device, task, user, etc.
    action = Column(String(20))  # 操作: view, create, update, delete
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    roles = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )


# 预定义权限
PERMISSIONS = {
    # 设备权限
    "device:view": ("设备查看", "查看设备列表和详情"),
    "device:create": ("设备创建", "创建新设备"),
    "device:update": ("设备更新", "更新设备信息"),
    "device:delete": ("设备删除", "删除设备"),
    "device:control": ("设备控制", "控制设备操作"),
    # 任务权限
    "task:view": ("任务查看", "查看任务列表和详情"),
    "task:create": ("任务创建", "创建新任务"),
    "task:update": ("任务更新", "更新任务信息"),
    "task:delete": ("任务删除", "删除任务"),
    "task:execute": ("任务执行", "执行任务"),
    # 用户权限
    "user:view": ("用户查看", "查看用户列表和详情"),
    "user:create": ("用户创建", "创建新用户"),
    "user:update": ("用户更新", "更新用户信息"),
    "user:delete": ("用户删除", "删除用户"),
    # 角色权限
    "role:view": ("角色查看", "查看角色列表和详情"),
    "role:create": ("角色创建", "创建新角色"),
    "role:update": ("角色更新", "更新角色信息"),
    "role:delete": ("角色删除", "删除角色"),
    # 系统设置权限
    "settings:view": ("设置查看", "查看系统设置"),
    "settings:update": ("设置更新", "更新系统设置"),
    # 监控告警权限
    "monitor:view": ("监控查看", "查看监控数据"),
    "monitor:manage": ("监控管理", "管理监控规则"),
    "alert:view": ("告警查看", "查看告警信息"),
    "alert:manage": ("告警管理", "管理告警规则"),
    # 数据导出权限
    "export:device": ("设备导出", "导出设备数据"),
    "export:task": ("任务导出", "导出任务数据"),
    "export:monitor": ("监控导出", "导出监控数据"),
    # 批量操作权限
    "batch:device": ("批量设备", "批量管理设备"),
    "batch:task": ("批量任务", "批量管理任务"),
}

# 预定义角色
ROLES = {
    "admin": {
        "name": "管理员",
        "description": "系统管理员,拥有所有权限",
        "permissions": list(PERMISSIONS.keys()),
    },
    "operator": {
        "name": "操作员",
        "description": "系统操作员,拥有基本操作权限",
        "permissions": [
            "device:view",
            "device:control",
            "task:view",
            "task:create",
            "task:execute",
            "monitor:view",
            "alert:view",
            "export:device",
            "export:task",
            "export:monitor",
        ],
    },
    "viewer": {
        "name": "访客",
        "description": "只读用户,只能查看数据",
        "permissions": ["device:view", "task:view", "monitor:view", "alert:view"],
    },
}
