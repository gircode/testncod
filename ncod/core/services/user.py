"""用户服务"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from ...models.user import User, UserMACAddress
from ...schemas.auth import UserCreate, UserUpdate
from ...core.security import get_password_hash
from ...core.errors.exceptions import ResourceNotFound, ResourceConflict
from ...utils.logger import logger


class UserService:
    """用户服务类"""

    @staticmethod
    async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
        """获取用户"""
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("获取用户失败", exc_info=True)
            raise

    @staticmethod
    async def get_users(
        db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """获取用户列表"""
        try:
            result = await db.execute(select(User).offset(skip).limit(limit))
            return result.scalars().all()
        except Exception as e:
            logger.error("获取用户列表失败", exc_info=True)
            raise

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """创建用户"""
        try:
            # 检查用户名和邮箱是否已存在
            result = await db.execute(
                select(User).where(
                    or_(
                        User.username == user_data.username,
                        User.email == user_data.email,
                    )
                )
            )
            if result.scalar_one_or_none():
                raise ResourceConflict("用户名或邮箱已存在")

            hashed_password = get_password_hash(user_data.password)
            user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            logger.error("创建用户失败", exc_info=True)
            raise

    @staticmethod
    async def update_user(
        db: AsyncSession, user_id: int, user_data: UserUpdate
    ) -> User:
        """更新用户"""
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise ResourceNotFound("用户不存在")

            update_data = user_data.model_dump(exclude_unset=True)
            if "password" in update_data:
                update_data["hashed_password"] = get_password_hash(
                    update_data.pop("password")
                )

            for field, value in update_data.items():
                setattr(user, field, value)

            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            await db.rollback()
            logger.error("更新用户失败", exc_info=True)
            raise
