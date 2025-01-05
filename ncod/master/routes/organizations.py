from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ncod.core.db.database import get_db
from ncod.master.models.organization import Organization
from ncod.master.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationTree,
)
from ncod.master.auth import get_current_user, check_admin

router = APIRouter(prefix="/api/v1/organizations", tags=["组织管理"])


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建组织"""
    # 检查权限
    check_admin(current_user)

    # 检查编码是否重复
    if db.query(Organization).filter(Organization.code == org_data.code).first():
        raise HTTPException(status_code=400, detail="Organization code already exists")

    new_org = Organization(**org_data.dict())
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    return new_org


@router.get("/tree", response_model=List[OrganizationTree])
async def get_organization_tree(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """获取组织架构树"""
    # 获取顶级组织
    root_orgs = db.query(Organization).filter(Organization.parent_id == None).all()

    return [build_org_tree(org, db) for org in root_orgs]


def build_org_tree(org: Organization, db: Session) -> OrganizationTree:
    """构建组织树结构"""
    children = db.query(Organization).filter(Organization.parent_id == org.id).all()

    return OrganizationTree(
        id=org.id,
        name=org.name,
        code=org.code,
        children=[build_org_tree(child, db) for child in children],
    )
