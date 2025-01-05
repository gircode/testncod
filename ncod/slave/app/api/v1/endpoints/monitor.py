"""
监控API路由
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.session import get_db
from ....services.health import HealthService
from ....services.monitor import MonitorService

router = APIRouter()


@router.get("/metrics")
async def get_metrics(
    page: int = Query(1, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    metric_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取监控指标"""
    monitor_service = MonitorService(db)
    return await monitor_service.get_metrics(
        page=page,
        page_size=page_size,
        start_time=start_time,
        end_time=end_time,
        metric_type=metric_type,
    )


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """获取活动告警"""
    monitor_service = MonitorService(db)
    return await monitor_service.get_active_alerts(
        severity=severity, alert_type=alert_type
    )


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int, db: AsyncSession = Depends(get_db)
) -> Dict[str, bool]:
    """解决告警"""
    monitor_service = MonitorService(db)
    success = await monitor_service.resolve_alert(alert_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Alert not found or already resolved"
        )
    return {"success": True}


@router.get("/health/check")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """健康检查"""
    health_service = HealthService(db)
    return await health_service.check()


@router.get("/health/summary")
async def system_summary(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """系统概况"""
    health_service = HealthService(db)
    return await health_service.get_system_summary()
