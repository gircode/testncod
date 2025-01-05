from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import or_

from ncod.core.db.database import get_db
from ncod.master.models.user import User, UserStatus
from ncod.master.models.organization import Organization
from ncod.master.schemas.user import UserResponse, UserUpdate
from ncod.master.auth import get_current_user, require_permissions
from ncod.master.models.permission import Permission
from ncod.master.models.user_assignment import UserAssignment

router = APIRouter(prefix="/api/v1/users", tags=["用户管理"])


@router.get("/others", response_model=List[UserResponse])
@require_permissions([Permission.USER_VIEW])
async def get_other_users(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """获取'其他'组织的用户列表"""
    other_org = Organization.get_or_create_other(db)

    query = db.query(User).filter(
        User.organization_id == other_org.id, User.status == UserStatus.PENDING
    )

    # 添加搜索条件
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.name.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%"),
            )
        )

    # 添加日期范围
    if start_date:
        query = query.filter(User.created_at >= start_date)
    if end_date:
        query = query.filter(User.created_at <= end_date)

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    return {"total": total, "items": users}


@router.post("/batch-assign")
@require_permissions([Permission.USER_MANAGE])
async def batch_assign_users(
    user_ids: List[int],
    organization_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """批量分配用户到组织"""
    # 验证目标组织
    target_org = (
        db.query(Organization).filter(Organization.id == organization_id).first()
    )
    if not target_org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # 检查权限(只能分配到自己管理的组织)
    if not current_user.is_admin and not _is_subordinate_org(
        db, current_user.organization_id, organization_id
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to assign to this organization"
        )

    # 获取其他组织
    other_org = Organization.get_or_create_other(db)

    # 更新用户
    users = (
        db.query(User)
        .filter(
            User.id.in_(user_ids),
            User.organization_id == other_org.id,
            User.status == UserStatus.PENDING,
        )
        .all()
    )

    if not users:
        raise HTTPException(status_code=400, detail="No valid users to assign")

    for user in users:
        user.organization_id = organization_id
        user.status = UserStatus.APPROVED

    db.commit()

    return {"message": f"Successfully assigned {len(users)} users"}


@router.post("/{user_id}/assign")
@require_permissions([Permission.USER_MANAGE])
async def assign_user(
    user_id: int,
    data: UserAssignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """分配单个用户到组织"""
    # 验证用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 验证目标组织
    target_org = (
        db.query(Organization).filter(Organization.id == data.organization_id).first()
    )
    if not target_org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # 检查权限
    if not current_user.is_admin and not _is_subordinate_org(
        db, current_user.organization_id, data.organization_id
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to assign to this organization"
        )

    # 检查用户是否在"其他"组织
    other_org = Organization.get_or_create_other(db)
    if user.organization_id != other_org.id or user.status != UserStatus.PENDING:
        raise HTTPException(
            status_code=400, detail="User is not available for assignment"
        )

    # 更新用户
    user.organization_id = data.organization_id
    user.status = UserStatus.APPROVED
    db.commit()

    # 添加分配记录
    assignment = UserAssignment(
        user_id=user.id,
        organization_id=data.organization_id,
        assigner_id=current_user.id,
        remark=data.remark,
    )
    db.add(assignment)
    db.commit()

    return {"message": "User assigned successfully"}


def _is_subordinate_org(db: Session, parent_id: int, child_id: int) -> bool:
    """检查是否是下级组织"""
    org = (
        db.query(Organization)
        .filter(Organization.id == child_id, Organization.parent_id == parent_id)
        .first()
    )
    return bool(org)
