"""角色API"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ncod.master.services.role import role_service
from ncod.master.middleware.auth import get_current_user, require_permissions
from ncod.core.logger import setup_logger

logger = setup_logger("role_api")
router = APIRouter(prefix="/api/v1/roles")


class RoleCreate(BaseModel):
    """创建角色请求"""

    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    is_system: bool = False


class RoleUpdate(BaseModel):
    """更新角色请求"""

    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


@router.post("")
@require_permissions(["role:create"])
async def create_role(request: RoleCreate, user: dict = Depends(get_current_user)):
    """创建角色"""
    try:
        success, message, role = await role_service.create_role(request.dict())
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        raise HTTPException(status_code=500, detail="Failed to create role")


@router.put("/{role_id}")
@require_permissions(["role:update"])
async def update_role(
    role_id: str, request: RoleUpdate, user: dict = Depends(get_current_user)
):
    """更新角色"""
    try:
        success, message, role = await role_service.update_role(
            role_id, request.dict(exclude_unset=True)
        )
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role: {e}")
        raise HTTPException(status_code=500, detail="Failed to update role")


@router.delete("/{role_id}")
@require_permissions(["role:delete"])
async def delete_role(role_id: str, user: dict = Depends(get_current_user)):
    """删除角色"""
    try:
        success, message = await role_service.delete_role(role_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"message": "Role deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting role: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete role")


@router.get("/{role_id}")
@require_permissions(["role:read"])
async def get_role(role_id: str, user: dict = Depends(get_current_user)):
    """获取角色"""
    try:
        role = await role_service.get_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting role: {e}")
        raise HTTPException(status_code=500, detail="Failed to get role")


@router.get("")
@require_permissions(["role:read"])
async def list_roles(
    include_system: bool = True, user: dict = Depends(get_current_user)
):
    """获取角色列表"""
    try:
        return await role_service.list_roles(include_system)
    except Exception as e:
        logger.error(f"Error listing roles: {e}")
        raise HTTPException(status_code=500, detail="Failed to list roles")
