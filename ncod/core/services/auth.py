"""认证服务"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from jose import jwt

from ncod.config.settings import settings
from ncod.core.security import verify_password, get_password_hash
from ncod.models.user import User
from ncod.models.mac_address import MacAddress
from ncod.schemas.user import UserCreate
from ncod.utils.logger import logger


class AuthService:
    @staticmethod
    async def authenticate_user(
        db: AsyncSession, username: str, password: str
    ) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
            )

        return user

    @staticmethod
    def create_access_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    async def verify_mac_address(
        db: AsyncSession, user_id: int, mac_address: str
    ) -> bool:
        result = await db.execute(
            select(MacAddress).where(
                MacAddress.user_id == user_id,
                MacAddress.mac_address == mac_address,
                MacAddress.is_active == True,
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def register_mac_address(
        db: AsyncSession, user_id: int, mac_address: str
    ) -> MacAddress:
        try:
            mac = MacAddress(user_id=user_id, mac_address=mac_address, is_active=True)
            db.add(mac)
            await db.commit()
            await db.refresh(mac)
            return mac
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """创建新用户"""
        try:
            # 检查用户名是否已存在
            result = await db.execute(
                select(User).where(User.username == user_data.username)
            )
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="用户名已存在"
                )

            # 检查邮箱是否已存在
            result = await db.execute(select(User).where(User.email == user_data.email))
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="邮箱已存在"
                )

            # 创建新用户
            user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=get_password_hash(user_data.password),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except HTTPException:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            raise
