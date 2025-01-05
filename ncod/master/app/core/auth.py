"""
认证相关功能
"""

import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

import aioredis
from app.core.config import settings
from app.core.token import TokenType, create_token, verify_token
from app.db.session import get_db
from app.models.auth import Permission, Role, User
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Redis连接
redis = aioredis.from_url(settings.REDIS_URL)


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
        payload = verify_token(token, expected_type=TokenType.ACCESS)
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # 检查令牌是否被撤销
        token_key = f"revoked_token:{token}"
        if await redis.exists(token_key):
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # 尝试从缓存获取用户
    user_key = f"user:{user_id}"
    cached_user = await redis.get(user_key)
    if cached_user:
        user_dict = json.loads(cached_user)
        return User(**user_dict)

    # 从数据库获取用户
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    # 缓存用户信息
    user_dict = {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "full_name": user.full_name,
        "roles": [{"id": r.id, "name": r.name} for r in user.roles],
    }
    await redis.set(user_key, json.dumps(user_dict), ex=settings.USER_CACHE_TTL)

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


async def check_resource_permission(
    resource: str, action: str, user: User, db: AsyncSession
) -> bool:
    """检查资源权限

    Args:
        resource: 资源名称
        action: 操作名称
        user: 用户对象
        db: 数据库会话

    Returns:
        bool: 是否有权限
    """
    # 超级管理员拥有所有权限
    if user.is_superuser:
        return True

    # 检查权限缓存
    perm_key = f"perm:{user.id}:{resource}:{action}"
    cached_perm = await redis.get(perm_key)
    if cached_perm is not None:
        return cached_perm == "1"

    # 检查用户角色权限
    has_permission = False
    for role in user.roles:
        for permission in role.permissions:
            if permission.resource == resource and permission.action == action:
                has_permission = True
                break
        if has_permission:
            break

    # 缓存权限结果
    await redis.set(
        perm_key, "1" if has_permission else "0", ex=settings.PERMISSION_CACHE_TTL
    )

    return has_permission


def check_resource_permission_decorator(resource: str, action: str):
    """资源权限检查装饰器

    Args:
        resource: 资源名称
        action: 操作名称
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
            **kwargs,
        ):
            if not await check_resource_permission(resource, action, current_user, db):
                raise HTTPException(
                    status_code=403, detail=f"无权访问资源 {resource}:{action}"
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def refresh_token(db: AsyncSession, refresh_token: str) -> Dict[str, str]:
    """刷新访问令牌

    Args:
        db: 数据库会话
        refresh_token: 刷新令牌

    Returns:
        Dict[str, str]: 新的访问令牌和刷新令牌
    """
    try:
        payload = verify_token(refresh_token, expected_type=TokenType.REFRESH)
        user_id: Optional[int] = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="无效的刷新令牌")

        # 检查刷新令牌是否被撤销
        token_key = f"revoked_token:{refresh_token}"
        if await redis.exists(token_key):
            raise HTTPException(status_code=400, detail="刷新令牌已被撤销")

        # 获取用户
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=400, detail="用户不存在或未激活")

        # 创建新的令牌
        access_token = create_token(
            subject=str(user.id),
            token_type=TokenType.ACCESS,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        new_refresh_token = create_token(
            subject=str(user.id),
            token_type=TokenType.REFRESH,
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        # 撤销旧的刷新令牌
        await redis.set(
            token_key, "1", ex=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    except JWTError:
        raise HTTPException(status_code=400, detail="无效的刷新令牌")


async def revoke_token(token: str):
    """撤销令牌

    Args:
        token: 要撤销的令牌
    """
    try:
        payload = verify_token(token)
        exp = payload.get("exp", 0)
        now = datetime.utcnow().timestamp()
        ttl = int(exp - now)

        if ttl > 0:
            token_key = f"revoked_token:{token}"
            await redis.set(token_key, "1", ex=ttl)

    except JWTError:
        pass  # 忽略无效的令牌
