"""权限路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ncod.core.deps import get_current_user, get_current_active_admin
from ncod.core.logger import setup_logger
from ncod.master.models.user import User
from ncod.master.services.permission import PermissionService
from ncod.master.schemas.permission import (
    PermissionCreate,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
)

router = APIRouter()
permission_service = PermissionService()
logger = setup_logger("permission_routes")


@router.get("/permissions", response_model=List[PermissionResponse])
async def get_permissions(current_user: User = Depends(get_current_active_admin)):
    """获取权限列表"""
    try:
        return await permission_service.get_permissions()
    except Exception as e:
        logger.error(f"Error getting permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get permissions",
        )


@router.post("/permissions", response_model=PermissionResponse)
async def create_permission(
    permission: PermissionCreate, current_user: User = Depends(get_current_active_admin)
):
    """创建权限"""
    try:
        return await permission_service.create_permission(permission)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create permission",
        )


@router.get("/roles", response_model=List[RoleResponse])
async def get_roles(current_user: User = Depends(get_current_user)):
    """获取角色列表"""
    try:
        return await permission_service.get_roles(
            organization_id=current_user.organization_id
        )
    except Exception as e:
        logger.error(f"Error getting roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get roles",
        )


@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role: RoleCreate, current_user: User = Depends(get_current_active_admin)
):
    """创建角色"""
    try:
        return await permission_service.create_role(role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create role",
        )
