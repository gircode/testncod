"""认证服务模块"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ncod.core.config import settings
from ncod.core.db import db
from ncod.models.user import User
from ncod.models.auth import UserMACAddress
from ncod.core.security import SecurityService
from ncod.utils.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


class AuthService:
    """认证服务类"""

    def __init__(self):
        self.security = SecurityService()
        self.max_mac_addresses = settings.MAX_DEVICES_PER_USER

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户"""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(User).where(User.username == username)
                )
                user = result.scalar_one_or_none()

                if not user or not self.security.verify_password(
                    password, user.hashed_password
                ):
                    return None

                return user
        except Exception as e:
            logger.error(f"用户认证失败: {str(e)}")
            return None

    async def create_access_token(
        self, user_id: int, expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode = {"sub": str(user_id), "exp": expire}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    async def register_mac_address(self, user_id: int, mac_address: str) -> bool:
        """注册MAC地址"""
        try:
            async with db.async_session() as session:
                user_macs = await self.get_user_mac_addresses(user_id)
                if len(user_macs) >= self.max_mac_addresses:
                    return False

                if mac_address in user_macs:
                    return True

                # 添加新MAC地址
                new_mac = UserMACAddress(
                    user_id=user_id,
                    mac_address=mac_address,
                    registered_at=datetime.utcnow(),
                )
                session.add(new_mac)
                await session.commit()
                return True

        except Exception as e:
            logger.error(f"MAC地址注册失败: {str(e)}")
            return False

    async def verify_mac_address(self, user_id: int, mac_address: str) -> bool:
        """验证MAC地址"""
        user_macs = await self.get_user_mac_addresses(user_id)
        return mac_address in user_macs

    async def get_user_mac_addresses(self, user_id: int) -> List[str]:
        """获取用户的MAC地址列表"""
        try:
            async with db.async_session() as session:
                result = await session.execute(
                    select(UserMACAddress).where(UserMACAddress.user_id == user_id)
                )
                mac_addresses = result.scalars().all()
                return [mac.mac_address for mac in mac_addresses]
        except Exception as e:
            logger.error(f"获取用户MAC地址失败: {str(e)}")
            return []


auth_service = AuthService()


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    async with db.async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        return user
