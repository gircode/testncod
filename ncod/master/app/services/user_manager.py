"""
用户管理服务
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.security import get_password_hash
from ..exceptions import UserError
from ..models.auth import Group, TempUser, User, UserPermission

logger = logging.getLogger(__name__)


class UserManager:
    """用户管理器"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_temp_user(
        self,
        username: str,
        password: str,
        group_id: int,
        creator_id: int,
        expires_at: datetime,
        device_ids: Optional[List[int]] = None,
        permissions: Optional[List[str]] = None,
    ) -> TempUser:
        """创建临时用户"""
        try:
            # 检查创建者权限
            creator = await self.db.get(User, creator_id)
            if not creator or not creator.is_admin:
                raise UserError("没有创建临时用户的权限")

            # 检查用户组
            group = await self.db.get(Group, group_id)
            if not group:
                raise UserError("用户组不存在")

            # 创建临时用户
            temp_user = TempUser(
                username=username,
                hashed_password=get_password_hash(password),
                group_id=group_id,
                creator_id=creator_id,
                expires_at=expires_at,
                is_active=True,
            )

            self.db.add(temp_user)
            await self.db.flush()

            # 添加设备权限
            if device_ids:
                for device_id in device_ids:
                    permission = UserPermission(
                        user_id=temp_user.id,
                        device_id=device_id,
                        permission_type="use",
                        granted_by=creator_id,
                        expires_at=expires_at,
                    )
                    self.db.add(permission)

            # 添加其他权限
            if permissions:
                for perm in permissions:
                    permission = UserPermission(
                        user_id=temp_user.id,
                        permission_type=perm,
                        granted_by=creator_id,
                        expires_at=expires_at,
                    )
                    self.db.add(permission)

            await self.db.commit()
            return temp_user

        except Exception as e:
            logger.error(f"创建临时用户失败: {str(e)}")
            await self.db.rollback()
            raise

    async def extend_temp_user(
        self, user_id: int, admin_id: int, new_expiry: datetime
    ) -> bool:
        """延长临时用户有效期"""
        try:
            # 检查管理员权限
            admin = await self.db.get(User, admin_id)
            if not admin or not admin.is_admin:
                raise UserError("没有延长临时用户有效期的权限")

            # 获取临时用户
            temp_user = await self.db.get(TempUser, user_id)
            if not temp_user:
                raise UserError("临时用户不存在")

            # 更新有效期
            temp_user.expires_at = new_expiry

            # 更新相关权限的有效期
            query = select(UserPermission).where(UserPermission.user_id == user_id)
            result = await self.db.execute(query)
            permissions = result.scalars().all()

            for perm in permissions:
                perm.expires_at = new_expiry

            await self.db.commit()
            return True

        except Exception as e:
            logger.error(f"延长临时用户有效期失败: {str(e)}")
            await self.db.rollback()
            return False

    async def deactivate_temp_user(
        self, user_id: int, admin_id: int, reason: str = "Administrative action"
    ) -> bool:
        """停用临时用户"""
        try:
            # 检查管理员权限
            admin = await self.db.get(User, admin_id)
            if not admin or not admin.is_admin:
                raise UserError("没有停用临时用户的权限")

            # 获取临时用户
            temp_user = await self.db.get(TempUser, user_id)
            if not temp_user:
                raise UserError("临时用户不存在")

            # 停用用户
            temp_user.is_active = False
            temp_user.deactivated_at = datetime.utcnow()
            temp_user.deactivated_by = admin_id
            temp_user.deactivation_reason = reason

            # 移除所有权限
            query = select(UserPermission).where(UserPermission.user_id == user_id)
            result = await self.db.execute(query)
            permissions = result.scalars().all()

            for perm in permissions:
                self.db.delete(perm)

            await self.db.commit()
            return True

        except Exception as e:
            logger.error(f"停用临时用户失败: {str(e)}")
            await self.db.rollback()
            return False

    async def get_temp_user_info(self, user_id: int) -> Optional[Dict]:
        """获取临时用户信息"""
        try:
            temp_user = await self.db.get(TempUser, user_id)
            if not temp_user:
                return None

            # 获取权限信息
            query = select(UserPermission).where(UserPermission.user_id == user_id)
            result = await self.db.execute(query)
            permissions = result.scalars().all()

            return {
                "id": temp_user.id,
                "username": temp_user.username,
                "group_id": temp_user.group_id,
                "creator_id": temp_user.creator_id,
                "created_at": temp_user.created_at,
                "expires_at": temp_user.expires_at,
                "is_active": temp_user.is_active,
                "deactivated_at": temp_user.deactivated_at,
                "deactivated_by": temp_user.deactivated_by,
                "deactivation_reason": temp_user.deactivation_reason,
                "permissions": [
                    {
                        "type": p.permission_type,
                        "device_id": p.device_id,
                        "granted_by": p.granted_by,
                        "expires_at": p.expires_at,
                    }
                    for p in permissions
                ],
            }

        except Exception as e:
            logger.error(f"获取临时用户信息失败: {str(e)}")
            return None

    async def cleanup_expired_users(self):
        """清理过期的临时用户"""
        try:
            current_time = datetime.utcnow()

            # 获取过期用户
            query = select(TempUser).where(
                and_(TempUser.is_active == True, TempUser.expires_at <= current_time)
            )
            result = await self.db.execute(query)
            expired_users = result.scalars().all()

            # 停用过期用户
            for user in expired_users:
                await self.deactivate_temp_user(
                    user.id, settings.SYSTEM_ADMIN_ID, "User expired"
                )

        except Exception as e:
            logger.error(f"清理过期用户失败: {str(e)}")

    async def start_cleanup_task(self):
        """启动清理任务"""
        while True:
            await self.cleanup_expired_users()
            await asyncio.sleep(settings.USER_CLEANUP_INTERVAL)
