"""权限检查中间件"""

from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from ncod.core.logger import setup_logger
from ncod.master.services.permission import PermissionService
from ncod.master.models.user import User

logger = setup_logger("permission_middleware")
permission_service = PermissionService()


async def get_user_from_request(request: Request) -> Optional[User]:
    """从请求中获取用户"""
    return getattr(request.state, "user", None)


def require_permission(resource_type: str, action: str):
    """权限检查装饰器"""

    async def permission_dependency(request: Request) -> None:
        user = await get_user_from_request(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )

        try:
            has_permission = await permission_service.check_permission(
                user_id=user.id, resource_type=resource_type, action=action
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
                )
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error checking permission",
            )

    return permission_dependency


class PermissionChecker:
    """权限检查器"""

    def __init__(self, resource_type: str):
        self.resource_type = resource_type

    def __call__(self, action: str, error_message: Optional[str] = None) -> Callable:
        """创建权限检查依赖项"""

        async def check_permission(request: Request) -> None:
            user = await get_user_from_request(request)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
                )

            try:
                has_permission = await permission_service.check_permission(
                    user_id=user.id, resource_type=self.resource_type, action=action
                )
                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=error_message or "Permission denied",
                    )
            except Exception as e:
                logger.error(f"Error checking permission: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error checking permission",
                )

        return check_permission
