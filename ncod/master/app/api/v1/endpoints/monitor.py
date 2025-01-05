"""
监控路由
"""

from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, cast

from app.core.config import settings
from app.core.deps import get_current_active_user, get_current_user
from app.core.security import check_admin_permission
from app.db.session import get_db
from app.models.auth import User
from app.models.monitor import DeviceUsage, MonitorAlert, MonitorMetric
from app.schemas.monitor import (
    DeviceUsageResponse,
    MonitorAlertResponse,
    MonitorMetricResponse,
)
from app.services.monitor import MonitorService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def check_resource_permission(resource: str, action: str):
    """资源权限检查装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
            **kwargs,
        ):
            if not await check_admin_permission(current_user):
                raise HTTPException(
                    status_code=403, detail=f"无权访问资源 {resource}:{action}"
                )
            return await func(*args, current_user=current_user, db=db, **kwargs)

        return wrapper

    return decorator


@router.get(
    "/metrics",
    response_model=List[MonitorMetricResponse],
    summary="获取监控指标",
    description="""
    获取系统监控指标。
    
    可以按照以下条件筛选：
    - 指标类型（cpu_usage, memory_usage, disk_usage等）
    - 时间范围
    - 分组
    
    需要 'monitor:view' 权限。
    """,
    responses={
        200: {
            "description": "成功获取监控指标",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "metric_type": "cpu_usage",
                            "value": 45.2,
                            "timestamp": "2024-01-20T10:30:00",
                            "group_id": 1,
                        }
                    ]
                }
            },
        },
        403: {"description": "权限不足"},
    },
)
@check_resource_permission("monitor", "view")
async def get_metrics(
    metric_type: Optional[str] = Query(None, description="指标类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    group_id: Optional[int] = Query(None, description="组ID"),
    limit: int = Query(100, description="返回结果数量限制"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[MonitorMetricResponse]:
    """
    获取监控指标

    - **metric_type**: 指标类型（可选）
    - **start_time**: 开始时间（可选）
    - **end_time**: 结束时间（可选）
    - **group_id**: 组ID（可选）
    - **limit**: 返回结果数量限制（默认100）
    """
    monitor_service = MonitorService(db)

    if group_id is None:
        group_id = cast(int, current_user.group_id)

    metrics = await monitor_service.get_metrics_by_group(
        group_id, metric_type, start_time, end_time, limit
    )
    return [MonitorMetricResponse.from_orm(metric) for metric in metrics]


@router.get(
    "/alerts",
    response_model=List[MonitorAlertResponse],
    summary="获取监控告警",
    description="""
    获取系统监控告警。
    
    可以按照以下条件筛选：
    - 告警类型
    - 是否已解决
    - 时间范围
    - 分组
    
    需要 'monitor:view' 权限。
    """,
    responses={
        200: {
            "description": "成功获取监控告警",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "alert_type": "cpu_usage",
                            "message": "CPU使用率过高: 95%",
                            "value": 95.0,
                            "resolved": False,
                            "created_at": "2024-01-20T10:30:00",
                            "resolved_at": None,
                            "group_id": 1,
                        }
                    ]
                }
            },
        },
        403: {"description": "权限不足"},
    },
)
@check_resource_permission("monitor", "view")
async def get_alerts(
    alert_type: Optional[str] = Query(None, description="告警类型"),
    resolved: Optional[bool] = Query(None, description="是否已解决"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    group_id: Optional[int] = Query(None, description="组ID"),
    limit: int = Query(100, description="返回结果数量限制"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[MonitorAlertResponse]:
    """
    获取监控告警

    - **alert_type**: 告警类型（可选）
    - **resolved**: 是否已解决（可选）
    - **start_time**: 开始时间（可选）
    - **end_time**: 结束时间（可选）
    - **group_id**: 组ID（可选）
    - **limit**: 返回结果数量限制（默认100）
    """
    monitor_service = MonitorService(db)

    if group_id is None:
        group_id = cast(int, current_user.group_id)

    alerts = await monitor_service.get_alerts_by_group(
        group_id, alert_type, resolved, start_time, end_time, limit
    )
    return [MonitorAlertResponse.from_orm(alert) for alert in alerts]


@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=MonitorAlertResponse,
    summary="解决告警",
    description="""
    将指定的告警标记为已解决。
    
    需要 'monitor:resolve' 权限。
    """,
    responses={
        200: {
            "description": "成功解决告警",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "alert_type": "cpu_usage",
                        "message": "CPU使用率过高: 95%",
                        "value": 95.0,
                        "resolved": True,
                        "created_at": "2024-01-20T10:30:00",
                        "resolved_at": "2024-01-20T10:35:00",
                        "group_id": 1,
                    }
                }
            },
        },
        403: {"description": "权限不足"},
        404: {"description": "告警不存在"},
    },
)
@check_resource_permission("monitor", "resolve")
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MonitorAlertResponse:
    """
    解决告警

    - **alert_id**: 告警ID
    """
    monitor_service = MonitorService(db)
    alert = await monitor_service.resolve_alert(alert_id)

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    return MonitorAlertResponse.from_orm(alert)


@router.get(
    "/device-usage",
    response_model=List[DeviceUsageResponse],
    summary="获取设备使用记录",
    description="""
    获取设备使用记录。
    
    可以按照以下条件筛选：
    - 设备ID
    - 用户ID
    - 时间范围
    - 是否活跃
    
    需要 'monitor:view' 权限。
    """,
    responses={
        200: {
            "description": "成功获取设备使用记录",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "device_id": 1,
                            "user_id": 1,
                            "start_time": "2024-01-20T10:00:00",
                            "end_time": "2024-01-20T11:00:00",
                            "group_id": 1,
                        }
                    ]
                }
            },
        },
        403: {"description": "权限不足"},
    },
)
@check_resource_permission("monitor", "view")
async def get_device_usage(
    device_id: Optional[int] = Query(None, description="设备ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    active_only: bool = Query(False, description="仅显示活跃记录"),
    group_id: Optional[int] = Query(None, description="组ID"),
    limit: int = Query(100, description="返回结果数量限制"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[DeviceUsageResponse]:
    """
    获取设备使用记录

    - **device_id**: 设备ID（可选）
    - **user_id**: 用户ID（可选）
    - **start_time**: 开始时间（可选）
    - **end_time**: 结束时间（可选）
    - **active_only**: 仅显示活跃记录（默认False）
    - **group_id**: 组ID（可选）
    - **limit**: 返回结果数量限制（默认100）
    """
    monitor_service = MonitorService(db)

    if group_id is None:
        group_id = cast(int, current_user.group_id)

    usage_records = await monitor_service.get_device_usage(
        group_id, device_id, user_id, start_time, end_time, active_only, limit
    )
    return [DeviceUsageResponse.from_orm(record) for record in usage_records]
