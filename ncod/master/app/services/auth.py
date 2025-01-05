"""
认证服务
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, cast

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.security import get_password_hash, verify_password
from ..models.models import DevicePermission, User

# 配置日志
logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(
        self,
        username: str,
        password: str,
        mac_address: Optional[str] = None,
        client_type: str = "web",
    ) -> Optional[User]:
        """用户认证"""
        try:
            # 获取用户
            result = await self.db.execute(select(User).where(User.email == username))
            user = result.scalar_one_or_none()

            if not user:
                return None

            # 验证密码
            if not verify_password(password, user.hashed_password):
                return None

            # 验证用户状态
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="用户未激活"
                )

            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            await self.db.commit()

            return user

        except Exception as e:
            logger.error(f"用户认证失败: {str(e)}")
            await self.db.rollback()
            raise

    async def get_current_user(self, token: str) -> Optional[User]:
        """获取当前用户"""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id = cast(int, payload.get("sub"))
            if user_id is None:
                return None

            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            return user

        except JWTError:
            return None

    async def check_permission(
        self, user: User, resource_type: str, resource_id: int, action: str
    ) -> bool:
        """检查权限"""
        # 超级管理员拥有所有权限
        if user.is_superuser:
            return True

        if resource_type == "device":
            # 检查设备权限
            result = await self.db.execute(
                select(DevicePermission).where(
                    and_(
                        DevicePermission.user_id == user.id,
                        DevicePermission.device_id == resource_id,
                        DevicePermission.action == action,
                    )
                )
            )
            permission = result.scalar_one_or_none()
            return bool(permission)

        elif resource_type == "user":
            # 用户只能管理自己
            return resource_id == user.id

        return False
