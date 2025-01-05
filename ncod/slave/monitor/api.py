"""监控API"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from ncod.slave.monitor.collector import metrics_collector
from ncod.slave.monitor.alert import alert_system
from ncod.slave.monitor.fault_handler import fault_handler
from ncod.slave.monitor.statistics import statistics_collector
from ncod.core.logger import setup_logger

logger = setup_logger("monitor_api")
router = APIRouter(prefix="/api/v1/monitor")


@router.get("/metrics/current")
async def get_current_metrics() -> Dict:
    """获取当前指标"""
    try:
        return metrics_collector.get_current_metrics()
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/device/{device_id}")
async def get_device_metrics(device_id: str) -> Dict:
    """获取设备指标"""
    try:
        metrics = metrics_collector.get_device_metrics(device_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Device not found")
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/active")
async def get_active_alerts() -> List:
    """获取活动告警"""
    try:
        return alert_system.get_active_alerts()
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/history")
async def get_alert_history(
    start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
) -> List:
    """获取告警历史"""
    try:
        return alert_system.get_alert_history(start_time, end_time)
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/faults/active")
async def get_active_faults() -> Dict:
    """获取活动故障"""
    try:
        return fault_handler.get_active_faults()
    except Exception as e:
        logger.error(f"Error getting active faults: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/device/{device_id}")
async def get_device_stats(device_id: str):
    """获取设备统计"""
    try:
        stats = statistics_collector.get_device_stats(device_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Device not found")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/user/{user_id}")
async def get_user_stats(user_id: str):
    """获取用户统计"""
    try:
        stats = statistics_collector.get_user_stats(user_id)
        if not stats:
            raise HTTPException(status_code=404, detail="User not found")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/hourly")
async def get_hourly_stats(
    start_hour: Optional[str] = None, end_hour: Optional[str] = None
) -> Dict:
    """获取小时统计"""
    try:
        return statistics_collector.get_hourly_stats(start_hour, end_hour)
    except Exception as e:
        logger.error(f"Error getting hourly stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/daily")
async def get_daily_stats(
    start_day: Optional[str] = None, end_day: Optional[str] = None
) -> Dict:
    """获取日统计"""
    try:
        return statistics_collector.get_daily_stats(start_day, end_day)
    except Exception as e:
        logger.error(f"Error getting daily stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_health_status() -> Dict:
    """获取健康状态"""
    try:
        metrics = metrics_collector.get_current_metrics()
        active_alerts = alert_system.get_active_alerts()
        active_faults = fault_handler.get_active_faults()

        return {
            "status": "healthy" if not (active_alerts or active_faults) else "warning",
            "metrics": {
                "cpu_usage": metrics.get("system", {}).get("cpu_usage", 0),
                "memory_usage": metrics.get("system", {}).get("memory_usage", 0),
                "active_devices": metrics.get("devices", {}).get("active_devices", 0),
            },
            "active_alerts": len(active_alerts),
            "active_faults": len(active_faults),
            "last_check": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
