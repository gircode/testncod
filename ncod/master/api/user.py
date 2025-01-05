"""用户API"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ncod.master.services.user import user_service
from ncod.master.middleware.auth import get_current_user, require_permissions
from ncod.core.logger import setup_logger

logger = setup_logger("user_api")
router = APIRouter(prefix="/api/v1/users")


class UserCreate(BaseModel):
    """创建用户请求"""

    username: str
    email: str
    password: str
    roles: Optional[List[str]] = None
    organizations: Optional[List[str]] = None


class UserUpdate(BaseModel):
    """更新用户请求"""

    email: Optional[str] = None
    roles: Optional[List[str]] = None
    organizations: Optional[List[str]] = None
    is_active: Optional[bool] = None


@router.post("")
@require_permissions(["user:create"])
async def create_user(request: UserCreate, user: dict = Depends(get_current_user)):
    """创建用户"""
    try:
        success, message, new_user = await user_service.create_user(request.dict())
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.put("/{user_id}")
@require_permissions(["user:update"])
async def update_user(
    user_id: str, request: UserUpdate, user: dict = Depends(get_current_user)
):
    """更新用户"""
    try:
        success, message, updated_user = await user_service.update_user(
            user_id, request.dict(exclude_unset=True)
        )
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.delete("/{user_id}")
@require_permissions(["user:delete"])
async def delete_user(user_id: str, user: dict = Depends(get_current_user)):
    """删除用户"""
    try:
        success, message = await user_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")


@router.get("/{user_id}")
@require_permissions(["user:read"])
async def get_user(user_id: str, user: dict = Depends(get_current_user)):
    """获取用户"""
    try:
        user_data = await user_service.get_user(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")


@router.get("")
@require_permissions(["user:read"])
async def list_users(user: dict = Depends(get_current_user)):
    """获取用户列表"""
    try:
        return await user_service.list_users()
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")
