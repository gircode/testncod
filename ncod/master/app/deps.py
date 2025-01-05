"""
依赖项
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from .core.config import settings
from .db.session import get_db
from .models.auth import User
from .services.auth import AuthService

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解码令牌
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # 获取用户
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(token)
        if user is None:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活动用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户未激活")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )
    return current_user


async def get_current_super_admin(
    current_user: User = Depends(get_current_admin_user),
) -> User:
    """获取当前超级管理员"""
    if current_user.admin_level != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限"
        )
    return current_user
