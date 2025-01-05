"""认证中间件"""

from typing import Optional, Callable
from functools import wraps
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ncod.master.services.auth import auth_service
from ncod.master.services.user import user_service
from ncod.core.logger import setup_logger

logger = setup_logger("auth_middleware")
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """获取当前用户"""
    try:
        success, message, user_id = auth_service.verify_token(credentials.credentials)
        if not success:
            raise HTTPException(status_code=401, detail=message)

        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if not user.get("is_active"):
            raise HTTPException(status_code=401, detail="Inactive user")

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication")


def require_permissions(permissions: list):
    """权限要求装饰器"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, user: dict = Depends(get_current_user), **kwargs):
            try:
                # 检查用户权限
                user_permissions = set()
                for role in user.get("roles", []):
                    # 这里需要从角色获取权限
                    role_permissions = await user_service.get_role_permissions(role)
                    user_permissions.update(role_permissions)

                if not all(perm in user_permissions for perm in permissions):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

                return await func(*args, user=user, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking permissions: {e}")
                raise HTTPException(status_code=403, detail="Permission check failed")

        return wrapper

    return decorator
