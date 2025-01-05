"""权限服务"""

from typing import Dict, List, Optional, Set
from ncod.core.logger import setup_logger
from ncod.core.cache.permission import permission_cache
from ncod.master.models.user import User
from ncod.master.models.role import Role
from ncod.master.models.permission import Permission
from ncod.core.db.transaction import transaction_manager

logger = setup_logger("permission_service")


class PermissionService:
    """权限服务"""

    def __init__(self):
        self.transaction = transaction_manager
        self.cache = permission_cache

    async def check_permission(
        self, user_id: str, required_permissions: List[str]
    ) -> bool:
        """检查用户权限"""
        try:
            # 先从缓存获取
            user_permissions = await self.cache.get_user_permissions(user_id)
            if not user_permissions:
                # 缓存未命中，从数据库获取
                user_permissions = await self._load_user_permissions(user_id)
                # 更新缓存
                await self.cache.set_user_permissions(user_id, user_permissions)

            # 检查权限
            user_perm_set = set(user_permissions)
            return all(perm in user_perm_set for perm in required_permissions)
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False

    async def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限"""
        try:
            # 先从缓存获取
            permissions = await self.cache.get_user_permissions(user_id)
            if not permissions:
                # 缓存未命中，从数据库获取
                permissions = await self._load_user_permissions(user_id)
                # 更新缓存
                await self.cache.set_user_permissions(user_id, permissions)
            return permissions
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return []

    async def _load_user_permissions(self, user_id: str) -> List[str]:
        """从数据库加载用户权限"""
        try:
            async with self.transaction.transaction() as session:
                # 获取用户
                user = await session.get(User, user_id)
                if not user:
                    return []

                # 获取用户所有角色的权限
                permissions: Set[str] = set()
                for role in user.roles:
                    role_perms = await self.cache.get_role_permissions(role.name)
                    if not role_perms:
                        role_perms = [p.code for p in role.permissions]
                        await self.cache.set_role_permissions(role.name, role_perms)
                    permissions.update(role_perms)

                return list(permissions)
        except Exception as e:
            logger.error(f"Error loading user permissions: {e}")
            return []

    async def refresh_user_permissions(self, user_id: str) -> bool:
        """刷新用户权限缓存"""
        try:
            # 删除旧缓存
            await self.cache.delete_user_permissions(user_id)
            # 重新加载权限
            permissions = await self._load_user_permissions(user_id)
            # 更新缓存
            return await self.cache.set_user_permissions(user_id, permissions)
        except Exception as e:
            logger.error(f"Error refreshing user permissions: {e}")
            return False

    async def refresh_role_permissions(self, role_name: str) -> bool:
        """刷新角色权限缓存"""
        try:
            async with self.transaction.transaction() as session:
                # 获取角色
                role = await Role.get_by_name(session, role_name)
                if not role:
                    return False

                # 更新角色权限缓存
                permissions = [p.code for p in role.permissions]
                await self.cache.set_role_permissions(role_name, permissions)

                # 获取角色下的所有用户
                for user in role.users:
                    await self.refresh_user_permissions(user.id)

                return True
        except Exception as e:
            logger.error(f"Error refreshing role permissions: {e}")
            return False


# 创建全局权限服务实例
permission_service = PermissionService()
