"""
依赖注入模块
"""

from typing import AsyncGenerator, Optional

from app.core.config import settings
from app.core.security import verify_token
from app.db.session import async_session
from app.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


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
        payload = verify_token(token)
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="用户不是超级管理员")
    return current_user
