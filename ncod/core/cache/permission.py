"""权限缓存"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from ncod.core.cache.base import BaseCache
from ncod.core.logger import setup_logger

logger = setup_logger("permission_cache")


class PermissionCache(BaseCache):
    """权限缓存"""

    def __init__(self):
        super().__init__()
        self.prefix = "permission:"
        self.expire = timedelta(minutes=30)

    async def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限"""
        try:
            key = f"{self.prefix}user:{user_id}"
            data = await self.get(key)
            return json.loads(data) if data else []
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return []

    async def set_user_permissions(self, user_id: str, permissions: List[str]) -> bool:
        """设置用户权限"""
        try:
            key = f"{self.prefix}user:{user_id}"
            return await self.set(key, json.dumps(permissions), expire=self.expire)
        except Exception as e:
            logger.error(f"Error setting user permissions: {e}")
            return False

    async def get_role_permissions(self, role_name: str) -> List[str]:
        """获取角色权限"""
        try:
            key = f"{self.prefix}role:{role_name}"
            data = await self.get(key)
            return json.loads(data) if data else []
        except Exception as e:
            logger.error(f"Error getting role permissions: {e}")
            return []

    async def set_role_permissions(
        self, role_name: str, permissions: List[str]
    ) -> bool:
        """设置角色权限"""
        try:
            key = f"{self.prefix}role:{role_name}"
            return await self.set(key, json.dumps(permissions), expire=self.expire)
        except Exception as e:
            logger.error(f"Error setting role permissions: {e}")
            return False

    async def delete_user_permissions(self, user_id: str) -> bool:
        """删除用户权限缓存"""
        try:
            key = f"{self.prefix}user:{user_id}"
            return await self.delete(key)
        except Exception as e:
            logger.error(f"Error deleting user permissions: {e}")
            return False

    async def delete_role_permissions(self, role_name: str) -> bool:
        """删除角色权限缓存"""
        try:
            key = f"{self.prefix}role:{role_name}"
            return await self.delete(key)
        except Exception as e:
            logger.error(f"Error deleting role permissions: {e}")
            return False


# 创建全局权限缓存实例
permission_cache = PermissionCache()
