"""
安全相关功能
"""

from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Set

from app.core.auth import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.auth import User
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


async def check_admin_permission(user: User) -> bool:
    """检查管理员权限"""
    return user.is_superuser or user.is_admin


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

    # 检查用户角色权限
    for role in user.roles:
        for permission in role.permissions:
            if permission.resource == resource and permission.action == action:
                return True

    return False


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
