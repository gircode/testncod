"""Auth模块"""

import logging
from functools import wraps
from typing import Any, Dict, List, Optional

from database import db_manager
from fastapi import Depends, HTTPException
from models.user import Device, DeviceGroup, User
from services.cache import cache

logger = logging.getLogger(__name__)

# 权限定义
PERMISSIONS = {
    # 设备权限
    "device": {
        "view": "device:view",
        "create": "device:create",
        "update": "device:update",
        "delete": "device:delete",
        "backup": "device:backup",
        "restore": "device:restore",
        "configure": "device:configure",
    },
    # 设备组权限
    "device_group": {
        "view": "device_group:view",
        "create": "device_group:create",
        "update": "device_group:update",
        "delete": "device_group:delete",
    },
    # 任务权限
    "task": {"view": "task:view", "create": "task:create", "cancel": "task:cancel"},
    # 告警权限
    "alert": {
        "view": "alert:view",
        "acknowledge": "alert:acknowledge",
        "resolve": "alert:resolve",
    },
    # 用户管理权限
    "user": {
        "view": "user:view",
        "create": "user:create",
        "update": "user:update",
        "delete": "user:delete",
    },
    # 系统管理权限
    "system": {
        "view": "system:view",
        "configure": "system:configure",
        "backup": "system:backup",
        "restore": "system:restore",
    },
}

# 角色定义
ROLES = {
    "admin": {
        "description": "系统管理员",
        "permissions": [
            # 设备权限
            "device:view",
            "device:create",
            "device:update",
            "device:delete",
            "device:backup",
            "device:restore",
            "device:configure",
            # 设备组权限
            "device_group:view",
            "device_group:create",
            "device_group:update",
            "device_group:delete",
            # 任务权限
            "task:view",
            "task:create",
            "task:cancel",
            # 告警权限
            "alert:view",
            "alert:acknowledge",
            "alert:resolve",
            # 用户管理权限
            "user:view",
            "user:create",
            "user:update",
            "user:delete",
            # 系统管理权限
            "system:view",
            "system:configure",
            "system:backup",
            "system:restore",
        ],
    },
    "operator": {
        "description": "运维人员",
        "permissions": [
            # 设备权限
            "device:view",
            "device:update",
            "device:backup",
            "device:configure",
            # 设备组权限
            "device_group:view",
            "device_group:update",
            # 任务权限
            "task:view",
            "task:create",
            "task:cancel",
            # 告警权限
            "alert:view",
            "alert:acknowledge",
            "alert:resolve",
            # 系统权限
            "system:view",
        ],
    },
    "viewer": {
        "description": "只读用户",
        "permissions": [
            # 设备权限
            "device:view",
            # 设备组权限
            "device_group:view",
            # 任务权限
            "task:view",
            # 告警权限
            "alert:view",
            # 系统权限
            "system:view",
        ],
    },
}


class PermissionError(Exception):
    """权限错误"""

    pass


class AuthService:
    """认证和授权服务"""

    @staticmethod
    async def get_user_permissions(user: User) -> List[str]:
        """获取用户权限列表"""
        try:
            # 尝试从缓存获取
            cached_permissions = await cache.get(f"user_permissions:{user.id}")
            if cached_permissions:
                return cached_permissions

            # 从数据库获取
            permissions = ROLES.get(user.role, {}).get("permissions", [])

            # 添加到缓存
            await cache.set(f"user_permissions:{user.id}", permissions)

            return permissions
        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return []

    @staticmethod
    async def check_permission(user: User, permission: str) -> bool:
        """检查用户是否有指定权限"""
        try:
            permissions = await AuthService.get_user_permissions(user)
            return permission in permissions
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False

    @staticmethod
    async def check_device_access(user: User, device: Device, permission: str) -> bool:
        """检查用户是否有设备的访问权限"""
        try:
            # 检查基本权限
            if not await AuthService.check_permission(user, f"device:{permission}"):
                return False

            # 检查设备关联
            return device in user.devices
        except Exception as e:
            logger.error(f"Device access check failed: {e}")
            return False

    @staticmethod
    async def check_group_access(
        user: User, group: DeviceGroup, permission: str
    ) -> bool:
        """检查用户是否有设备组的访问权限"""
        try:
            # 检查基本权限
            if not await AuthService.check_permission(
                user, f"device_group:{permission}"
            ):
                return False

            # 检查是否有组内任意设备的访问权限
            return any(device in user.devices for device in group.devices)
        except Exception as e:
            logger.error(f"Group access check failed: {e}")
            return False


def require_permission(permission: str):
    """权限检查装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户
            user = kwargs.get("user")
            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")

            # 检查权限
            if not await AuthService.check_permission(user, permission):
                raise HTTPException(status_code=403, detail="Permission denied")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_device_permission(permission: str):
    """设备权限检查装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户和设备
            user = kwargs.get("user")
            device = kwargs.get("device")

            if not user or not device:
                raise HTTPException(status_code=401, detail="Unauthorized")

            # 检查设备权限
            if not await AuthService.check_device_access(user, device, permission):
                raise HTTPException(status_code=403, detail="Permission denied")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_group_permission(permission: str):
    """设备组权限检查装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户和设备组
            user = kwargs.get("user")
            group = kwargs.get("group")

            if not user or not group:
                raise HTTPException(status_code=401, detail="Unauthorized")

            # 检查设备组权限
            if not await AuthService.check_group_access(user, group, permission):
                raise HTTPException(status_code=403, detail="Permission denied")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# 创建权限服务实例
auth_service = AuthService()
