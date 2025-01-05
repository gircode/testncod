"""Permissions模块"""

import logging
from functools import wraps
from typing import Callable, Dict, List, Optional

import jwt
from flask import abort, request, session

logger = logging.getLogger(__name__)


class Permission:
    """权限类"""

    def __init__(self, code: str, name: str, description: str = None):
        self.code = code
        self.name = name
        self.description = description


class Role:
    """角色类"""

    def __init__(self, code: str, name: str, permissions: List[str]):
        self.code = code
        self.name = name
        self.permissions = permissions


class PermissionManager:
    """权限管理器"""

    def __init__(self):
        self._permissions: Dict[str, Permission] = {}
        self._roles: Dict[str, Role] = {}
        self._user_roles: Dict[int, List[str]] = {}

        # 初始化基础权限
        self._init_permissions()
        self._init_roles()

    def _init_permissions(self):
        """初始化权限"""
        # 系统管理权限
        self.register_permission("SYSTEM_ADMIN", "系统管理", "系统管理相关权限")
        self.register_permission("USER_ADMIN", "用户管理", "用户管理相关权限")
        self.register_permission("ROLE_ADMIN", "角色管理", "角色管理相关权限")

        # 设备管理权限
        self.register_permission("DEVICE_VIEW", "查看设备", "查看设备信息")
        self.register_permission("DEVICE_ADD", "添加设备", "添加新设备")
        self.register_permission("DEVICE_EDIT", "编辑设备", "编辑设备信息")
        self.register_permission("DEVICE_DELETE", "删除设备", "删除设备")
        self.register_permission("DEVICE_CONTROL", "控制设备", "控制设备操作")

        # 任务管理权限
        self.register_permission("TASK_VIEW", "查看任务", "查看任务信息")
        self.register_permission("TASK_ADD", "添加任务", "添加新任务")
        self.register_permission("TASK_EDIT", "编辑任务", "编辑任务信息")
        self.register_permission("TASK_DELETE", "删除任务", "删除任务")

        # 数据管理权限
        self.register_permission("DATA_EXPORT", "数据导出", "导出系统数据")
        self.register_permission("DATA_IMPORT", "数据导入", "导入系统数据")

        # 监控管理权限
        self.register_permission("MONITOR_VIEW", "查看监控", "查看监控信息")
        self.register_permission("MONITOR_MANAGE", "管理监控", "管理监控规则")

        # 日志管理权限
        self.register_permission("LOG_VIEW", "查看日志", "查看系统日志")
        self.register_permission("LOG_MANAGE", "管理日志", "管理日志配置")

    def _init_roles(self):
        """初始化角色"""
        # 超级管理员
        self.register_role(
            "SUPER_ADMIN",
            "超级管理员",
            [
                "SYSTEM_ADMIN",
                "USER_ADMIN",
                "ROLE_ADMIN",
                "DEVICE_VIEW",
                "DEVICE_ADD",
                "DEVICE_EDIT",
                "DEVICE_DELETE",
                "DEVICE_CONTROL",
                "TASK_VIEW",
                "TASK_ADD",
                "TASK_EDIT",
                "TASK_DELETE",
                "DATA_EXPORT",
                "DATA_IMPORT",
                "MONITOR_VIEW",
                "MONITOR_MANAGE",
                "LOG_VIEW",
                "LOG_MANAGE",
            ],
        )

        # 设备管理员
        self.register_role(
            "DEVICE_ADMIN",
            "设备管理员",
            [
                "DEVICE_VIEW",
                "DEVICE_ADD",
                "DEVICE_EDIT",
                "DEVICE_DELETE",
                "DEVICE_CONTROL",
                "TASK_VIEW",
                "TASK_ADD",
                "TASK_EDIT",
                "MONITOR_VIEW",
                "LOG_VIEW",
            ],
        )

        # 普通用户
        self.register_role(
            "NORMAL_USER",
            "普通用户",
            ["DEVICE_VIEW", "DEVICE_CONTROL", "TASK_VIEW", "MONITOR_VIEW"],
        )

    def register_permission(self, code: str, name: str, description: str = None):
        """注册权限"""
        self._permissions[code] = Permission(code, name, description)

    def register_role(self, code: str, name: str, permissions: List[str]):
        """注册角色"""
        self._roles[code] = Role(code, name, permissions)

    def assign_roles(self, user_id: int, role_codes: List[str]):
        """分配角色给用户"""
        self._user_roles[user_id] = role_codes

    def get_user_permissions(self, user_id: int) -> List[str]:
        """获取用户权限"""
        permissions = set()

        # 获取用户角色
        role_codes = self._user_roles.get(user_id, [])

        # 获取角色对应的权限
        for role_code in role_codes:
            role = self._roles.get(role_code)
            if role:
                permissions.update(role.permissions)

        return list(permissions)

    def has_permission(self, user_id: int, permission: str) -> bool:
        """检查用户是否有指定权限"""
        return permission in self.get_user_permissions(user_id)

    def has_any_permission(self, user_id: int, permissions: List[str]) -> bool:
        """检查用户是否有任意一个指定权限"""
        user_permissions = self.get_user_permissions(user_id)
        return any(p in user_permissions for p in permissions)

    def has_all_permissions(self, user_id: int, permissions: List[str]) -> bool:
        """检查用户是否有所有指定权限"""
        user_permissions = self.get_user_permissions(user_id)
        return all(p in user_permissions for p in permissions)


# 创建全局权限管理器实例
permission_manager = PermissionManager()


def login_required(f: Callable) -> Callable:
    """登录验证装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session中是否有user_id
        if "user_id" not in session:
            abort(401)
        return f(*args, **kwargs)

    return decorated_function


def permission_required(permission: str) -> Callable:
    """权限验证装饰器"""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查session中是否有user_id
            if "user_id" not in session:
                abort(401)

            user_id = session["user_id"]

            # 检查权限
            if not permission_manager.has_permission(user_id, permission):
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def any_permission_required(permissions: List[str]) -> Callable:
    """任意权限验证装饰器"""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                abort(401)

            user_id = session["user_id"]

            # 检查是否有任意一个权限
            if not permission_manager.has_any_permission(user_id, permissions):
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def all_permissions_required(permissions: List[str]) -> Callable:
    """所有权限验证装饰器"""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                abort(401)

            user_id = session["user_id"]

            # 检查是否有所有权限
            if not permission_manager.has_all_permissions(user_id, permissions):
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def role_required(role: str) -> Callable:
    """角色验证装饰器"""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                abort(401)

            user_id = session["user_id"]

            # 检查用户角色
            user_roles = permission_manager._user_roles.get(user_id, [])
            if role not in user_roles:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def verify_jwt_token(token: str) -> Optional[Dict]:
    """验证JWT令牌"""
    try:
        # 这里需要配置密钥
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None


def get_current_user_id() -> Optional[int]:
    """获取当前用户ID"""
    return session.get("user_id")


def get_current_user_permissions() -> List[str]:
    """获取当前用户权限"""
    user_id = get_current_user_id()
    if user_id is None:
        return []
    return permission_manager.get_user_permissions(user_id)
