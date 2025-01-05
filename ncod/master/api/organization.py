"""组织API"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ncod.master.services.organization import organization_service
from ncod.master.middleware.auth import get_current_user, require_permissions
from ncod.core.logger import setup_logger

logger = setup_logger("organization_api")
router = APIRouter(prefix="/api/v1/organizations")


class OrganizationCreate(BaseModel):
    """创建组织请求"""

    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[str] = None


class OrganizationUpdate(BaseModel):
    """更新组织请求"""

    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None


@router.post("")
@require_permissions(["organization:create"])
async def create_organization(
    request: OrganizationCreate, user: dict = Depends(get_current_user)
):
    """创建组织"""
    try:
        success, message, org = await organization_service.create_organization(
            request.dict()
        )
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return org
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        raise HTTPException(status_code=500, detail="Failed to create organization")


@router.put("/{org_id}")
@require_permissions(["organization:update"])
async def update_organization(
    org_id: str, request: OrganizationUpdate, user: dict = Depends(get_current_user)
):
    """更新组织"""
    try:
        success, message, org = await organization_service.update_organization(
            org_id, request.dict(exclude_unset=True)
        )
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return org
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating organization: {e}")
        raise HTTPException(status_code=500, detail="Failed to update organization")


@router.delete("/{org_id}")
@require_permissions(["organization:delete"])
async def delete_organization(org_id: str, user: dict = Depends(get_current_user)):
    """删除组织"""
    try:
        success, message = await organization_service.delete_organization(org_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"message": "Organization deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting organization: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete organization")


@router.get("/{org_id}")
@require_permissions(["organization:read"])
async def get_organization(org_id: str, user: dict = Depends(get_current_user)):
    """获取组织"""
    try:
        org = await organization_service.get_organization(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting organization: {e}")
        raise HTTPException(status_code=500, detail="Failed to get organization")


@router.get("")
@require_permissions(["organization:read"])
async def list_organizations(
    parent_id: Optional[str] = None, user: dict = Depends(get_current_user)
):
    """获取组织列表"""
    try:
        return await organization_service.list_organizations(parent_id)
    except Exception as e:
        logger.error(f"Error listing organizations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list organizations")


@router.get("/tree")
@require_permissions(["organization:read"])
async def get_organization_tree(
    org_id: Optional[str] = None, user: dict = Depends(get_current_user)
):
    """获取组织树"""
    try:
        return await organization_service.get_organization_tree(org_id)
    except Exception as e:
        logger.error(f"Error getting organization tree: {e}")
        raise HTTPException(status_code=500, detail="Failed to get organization tree")
