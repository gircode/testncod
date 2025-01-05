"""组织路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ncod.core.deps import get_current_user, get_current_active_admin
from ncod.core.logger import master_logger as logger
from ncod.master.models.user import User
from ncod.master.services.organization import OrganizationService
from ncod.master.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationTree,
)

router = APIRouter()
org_service = OrganizationService()


@router.get("/", response_model=List[OrganizationResponse])
async def get_organizations(
    current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 100
):
    """获取组织列表"""
    try:
        return await org_service.get_organizations(skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting organizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organizations",
        )


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org: OrganizationCreate, current_user: User = Depends(get_current_active_admin)
):
    """创建组织"""
    try:
        return await org_service.create_organization(org)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization",
        )


@router.get("/tree", response_model=List[OrganizationTree])
async def get_organization_tree(current_user: User = Depends(get_current_user)):
    """获取组织树"""
    try:
        return await org_service.get_organization_tree()
    except Exception as e:
        logger.error(f"Error getting organization tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization tree",
        )


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(org_id: str, current_user: User = Depends(get_current_user)):
    """获取组织详情"""
    org = await org_service.get_organization(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    return org


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    org_update: OrganizationUpdate,
    current_user: User = Depends(get_current_active_admin),
):
    """更新组织"""
    try:
        org = await org_service.update_organization(org_id, org_update)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )
        return org
    except Exception as e:
        logger.error(f"Error updating organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization",
        )
