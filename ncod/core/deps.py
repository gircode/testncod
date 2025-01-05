"""依赖项模块"""

from typing import Optional, Annotated, AsyncGenerator, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from ncod.core.logger import setup_logger
from ncod.core.auth.jwt_handler import decode_jwt_token
from ncod.master.models.user import User
from ncod.master.services.user import UserService
from ncod.master.services.permission import PermissionService
from ncod.core.cache.manager import CacheManager

logger = setup_logger("deps")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
user_service = UserService()
permission_service = PermissionService()

# 创建缓存管理器实例
cache_manager = CacheManager()


async def get_cache() -> AsyncGenerator[CacheManager, None]:
    """获取缓存管理器"""
    yield cache_manager


# 依赖注入函数类型
Cache = Callable[[], AsyncGenerator[CacheManager, None]]

# 创建依赖实例
get_cache_manager = get_cache


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_jwt_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_service.get_user(user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_active_admin(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """获取当前管理员用户"""
    try:
        is_admin = await permission_service.check_permission(
            user_id=current_user.id, resource_type="system", action="admin"
        )
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
            )
        return current_user
    except Exception as e:
        logger.error(f"Error checking admin permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking permissions",
        )


def get_permission_checker(resource_type: str):
    """获取权限检查器"""
    from ncod.core.middleware.permission import PermissionChecker

    return PermissionChecker(resource_type)
