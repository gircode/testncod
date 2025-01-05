"""用户管理路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ncod.core.deps import (
    get_current_user,
    get_current_active_admin,
    get_permission_checker,
)
from ncod.core.logger import setup_logger
from ncod.master.models.user import User
from ncod.master.services.user import UserService
from ncod.master.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter()
user_service = UserService()
logger = setup_logger("user_routes")

# 创建权限检查器
user_permission = get_permission_checker("user")


@router.get(
    "/",
    response_model=List[UserResponse],
    dependencies=[Depends(user_permission("view"))],
)
async def get_users(
    current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 100
):
    """获取用户列表"""
    try:
        return await user_service.get_users(
            organization_id=current_user.organization_id, skip=skip, limit=limit
        )
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users",
        )


@router.post(
    "/", response_model=UserResponse, dependencies=[Depends(user_permission("manage"))]
)
async def create_user(
    user: UserCreate, current_user: User = Depends(get_current_active_admin)
):
    """创建用户"""
    try:
        # 检查组织权限
        if user.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create user in this organization",
            )

        return await user_service.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(user_permission("view"))],
)
async def get_user(user_id: str, current_user: User = Depends(get_current_user)):
    """获取用户详情"""
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user",
        )
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(user_permission("manage"))],
)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_admin),
):
    """更新用户"""
    try:
        # 获取用户
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # 检查组织权限
        if user.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user",
            )

        # 更新用户
        updated_user = await user_service.update_user(user_id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user
