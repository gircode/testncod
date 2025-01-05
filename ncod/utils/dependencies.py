from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ncod.utils.security import verify_token
from ncod.utils.db import get_db
from ncod.utils.cache import redis_cache
from ncod.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db=Depends(get_db)
) -> User:
    """获取当前用户

    Args:
        token: 访问令牌
        db: 数据库会话

    Returns:
        User: 当前用户

    Raises:
        HTTPException: 认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # 尝试从缓存获取用户
    cache_key = f"user:{user_id}"
    user_data = await redis_cache.get(cache_key)

    if user_data:
        return User(**user_data)

    # 从数据库获取用户
    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception

    # 缓存用户数据
    await redis_cache.set(cache_key, user.dict(), expire=3600)  # 1小时

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """获取当前活跃用户

    Args:
        current_user: 当前用户

    Returns:
        User: 当前活跃用户

    Raises:
        HTTPException: 用户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """获取当前管理员用户

    Args:
        current_user: 当前用户

    Returns:
        User: 当前管理员用户

    Raises:
        HTTPException: 权限不足
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    return current_user
