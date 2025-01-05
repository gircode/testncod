"""
审计日志API端点
"""

from datetime import datetime
from typing import Any, Optional

from app.core.auth import get_current_superuser, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.audit import (
    AuditLogListResponse,
    AuditLogResponse,
    SecurityMetricsResponse,
    UserActivityResponse,
)
from app.services.audit import AuditService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
) -> Any:
    """
    获取审计日志列表（仅超级管理员）
    """
    service = AuditService(db)
    logs, total = await service.get_logs(
        page=page,
        per_page=per_page,
        user_id=user_id,
        action=action,
        status=status,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )

    return {
        "items": logs,
        "total": total,
        "page": page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/me", response_model=AuditLogListResponse)
async def get_my_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    status: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Any:
    """
    获取当前用户的审计日志
    """
    service = AuditService(db)
    logs, total = await service.get_logs(
        page=page,
        per_page=per_page,
        user_id=current_user.id,
        action=action,
        status=status,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "items": logs,
        "total": total,
        "page": page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/users/{user_id}/activity", response_model=UserActivityResponse)
async def get_user_activity(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
    days: int = Query(30, ge=1, le=365),
) -> Any:
    """
    获取用户活动统计（仅超级管理员）
    """
    service = AuditService(db)
    return await service.get_user_activity(user_id, days)


@router.get("/me/activity", response_model=UserActivityResponse)
async def get_my_activity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
) -> Any:
    """
    获取当前用户的活动统计
    """
    service = AuditService(db)
    return await service.get_user_activity(current_user.id, days)


@router.get("/security/metrics", response_model=SecurityMetricsResponse)
async def get_security_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
    days: int = Query(30, ge=1, le=365),
) -> Any:
    """
    获取安全指标（仅超级管理员）
    """
    service = AuditService(db)
    return await service.get_security_metrics(days)


@router.post("/cleanup", response_model=dict)
async def cleanup_audit_logs(
    days: int = Query(..., ge=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
) -> Any:
    """
    清理旧的审计日志（仅超级管理员）
    """
    service = AuditService(db)
    deleted_count = await service.cleanup_old_logs(days)

    return {
        "message": f"Successfully deleted {deleted_count} old audit logs",
        "deleted_count": deleted_count,
    }
