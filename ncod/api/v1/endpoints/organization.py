"""组织管理路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ncod.core.db.base import get_db
from ncod.core.auth import get_current_user, check_permission
from ncod.common.services.organization import OrganizationService
from ncod.schemas.organization import (
    GroupCreate,
    GroupResponse,
    DepartmentCreate,
    DepartmentResponse,
)
from ncod.utils.logger import logger

router = APIRouter()


@router.post("/groups", response_model=GroupResponse)
async def create_group(
    group_data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建大组"""
    await check_permission(
        user=current_user, db=db, resource_type="group", resource_id=0, action="create"
    )

    org_service = OrganizationService(db)
    group = await org_service.create_group(
        name=group_data.name, code=group_data.code, description=group_data.description
    )

    if not group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="大组创建失败"
        )
    return group


@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    dept_data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建部门"""
    await check_permission(
        user=current_user,
        db=db,
        resource_type="department",
        resource_id=0,
        action="create",
    )

    org_service = OrganizationService(db)
    department = await org_service.create_department(
        name=dept_data.name,
        group_id=dept_data.group_id,
        parent_id=dept_data.parent_id,
        level=dept_data.level,
    )

    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="部门创建失败"
        )
    return department


@router.get("/groups/{group_id}/departments")
async def get_department_tree(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取部门树结构"""
    await check_permission(
        user=current_user,
        db=db,
        resource_type="group",
        resource_id=group_id,
        action="view",
    )

    org_service = OrganizationService(db)
    tree = await org_service.get_department_tree(group_id)
    return tree
