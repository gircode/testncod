"""
注册相关路由
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.session import get_db
from ....deps import get_current_admin_user
from ....models.auth import User
from ....services.registration import RegistrationService

router = APIRouter()


class RegistrationRequest(BaseModel):
    """注册请求"""

    username: str
    email: EmailStr
    password: str
    department_id: int
    group_id: int


class VerificationRequest(BaseModel):
    """验证请求"""

    request_id: int
    verification_code: str


class ApprovalRequest(BaseModel):
    """批准请求"""

    request_id: int
    is_temporary: bool = False
    valid_days: int | None = None


class RejectionRequest(BaseModel):
    """拒绝请求"""

    request_id: int
    remarks: str | None = None


@router.post("/request")
async def request_registration(
    *, db: AsyncSession = Depends(get_db), request: RegistrationRequest, client_ip: str
) -> Any:
    """申请注册"""
    registration_service = RegistrationService(db)
    return await registration_service.request_registration(
        username=request.username,
        email=request.email,
        password=request.password,
        department_id=request.department_id,
        group_id=request.group_id,
        registration_ip=client_ip,
    )


@router.post("/verify")
async def verify_email(
    *, db: AsyncSession = Depends(get_db), request: VerificationRequest
) -> Any:
    """验证邮箱"""
    registration_service = RegistrationService(db)
    return await registration_service.verify_email(
        request_id=request.request_id, verification_code=request.verification_code
    )


@router.post("/approve")
async def approve_registration(
    *,
    db: AsyncSession = Depends(get_db),
    request: ApprovalRequest,
    current_admin: User = Depends(get_current_admin_user),
) -> Any:
    """批准注册"""
    registration_service = RegistrationService(db)
    return await registration_service.approve_registration(
        request_id=request.request_id,
        admin_id=current_admin.id,
        is_temporary=request.is_temporary,
        valid_days=request.valid_days,
    )


@router.post("/reject")
async def reject_registration(
    *,
    db: AsyncSession = Depends(get_db),
    request: RejectionRequest,
    current_admin: User = Depends(get_current_admin_user),
) -> Any:
    """拒绝注册"""
    registration_service = RegistrationService(db)
    return await registration_service.reject_registration(
        request_id=request.request_id,
        admin_id=current_admin.id,
        remarks=request.remarks,
    )


@router.get("/pending")
async def get_pending_requests(
    *,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """获取待处理的注册申请"""
    registration_service = RegistrationService(db)
    return await registration_service.get_pending_requests(skip=skip, limit=limit)
