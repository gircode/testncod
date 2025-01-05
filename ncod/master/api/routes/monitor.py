"""监控API路由"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from ncod.master.services.monitor import monitor_service
from ncod.master.middleware.auth import get_current_user, require_permissions
from ncod.core.logger import setup_logger

logger = setup_logger("monitor_api")
router = APIRouter(prefix="/api/v1/monitor")


@router.post("/metrics/{device_id}")
@require_permissions(["monitor:write"])
async def record_device_metrics(
    device_id: str, metrics: dict, user: dict = Depends(get_current_user)
):
    """记录设备指标"""
    try:
        success = await monitor_service.record_device_metrics(device_id, metrics)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to record metrics")
        return {"message": "Metrics recorded successfully"}
    except Exception as e:
        logger.error(f"Error recording metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to record metrics")


@router.get("/metrics/{device_id}")
@require_permissions(["monitor:read"])
async def get_device_metrics(
    device_id: str,
    metric_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user: dict = Depends(get_current_user),
):
    """获取设备指标"""
    try:
        return await monitor_service.get_device_metrics(
            device_id, metric_type, start_time, end_time
        )
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@router.post("/alerts/{device_id}")
@require_permissions(["monitor:write"])
async def create_device_alert(
    device_id: str,
    alert_type: str,
    level: str,
    message: str,
    user: dict = Depends(get_current_user),
):
    """创建设备告警"""
    try:
        success = await monitor_service.create_alert(
            device_id, alert_type, level, message
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create alert")
        return {"message": "Alert created successfully"}
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@router.get("/alerts/{device_id}")
@require_permissions(["monitor:read"])
async def get_device_alerts(
    device_id: str,
    alert_type: Optional[str] = None,
    level: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    user: dict = Depends(get_current_user),
):
    """获取设备告警"""
    try:
        return await monitor_service.get_device_alerts(
            device_id, alert_type, level, is_resolved
        )
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")
