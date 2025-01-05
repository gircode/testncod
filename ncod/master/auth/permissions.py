from functools import wraps
from typing import List, Union
from fastapi import HTTPException, Depends
from ncod.master.models.permission import Permission
from ncod.master.auth import get_current_user


def require_permissions(
    permissions: Union[Permission, List[Permission]], require_all: bool = False
):
    """
    权限检查装饰器

    Args:
        permissions: 单个权限或权限列表
        require_all: True表示需要所有权限，False表示只需要其中一个权限
    """
    if isinstance(permissions, Permission):
        permissions = [permissions]

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
            if not current_user:
                raise HTTPException(status_code=401, detail="Not authenticated")

            # 系统管理员拥有所有权限
            if current_user.has_permission(Permission.ADMIN):
                return await func(*args, current_user=current_user, **kwargs)

            if require_all:
                # 需要所有权限
                if not all(current_user.has_permission(p) for p in permissions):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )
            else:
                # 只需要其中一个权限
                if not any(current_user.has_permission(p) for p in permissions):
                    raise HTTPException(
                        status_code=403, detail="Insufficient permissions"
                    )

            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator
