from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..core.auth import get_current_admin_user
from ..models.user import User
from ..monitoring.collector import MetricsCollector
from ..schemas.monitoring import (
    TimeRange,
    DeviceMetricsResponse,
    SlaveMetricsResponse,
    SystemMetricsResponse,
)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# 初始化监控收集器
metrics_collector = MetricsCollector(
    {"metrics_collection_interval": 60, "metrics_retention_days": 30}
)


@router.on_event("startup")
async def startup_monitoring():
    """启动监控系统"""
    await metrics_collector.start()


@router.on_event("shutdown")
async def shutdown_monitoring():
    """关闭监控系统"""
    await metrics_collector.stop()


@router.get("/device/{device_id}", response_model=DeviceMetricsResponse)
async def get_device_metrics(
    device_id: int,
    time_range: TimeRange = Query(...),
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """获取设备监控数据"""
    try:
        end_time = datetime.now()
        if time_range == TimeRange.HOUR:
            start_time = end_time - timedelta(hours=1)
        elif time_range == TimeRange.DAY:
            start_time = end_time - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            start_time = end_time - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH:
            start_time = end_time - timedelta(days=30)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid time range"
            )

        metrics = await metrics_collector.get_device_metrics(
            device_id, start_time, end_time
        )

        return {"device_id": device_id, "time_range": time_range, "metrics": metrics}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/slave/{slave_id}", response_model=SlaveMetricsResponse)
async def get_slave_metrics(
    slave_id: int,
    time_range: TimeRange = Query(...),
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """获取从服务器监控数据"""
    try:
        end_time = datetime.now()
        if time_range == TimeRange.HOUR:
            start_time = end_time - timedelta(hours=1)
        elif time_range == TimeRange.DAY:
            start_time = end_time - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            start_time = end_time - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH:
            start_time = end_time - timedelta(days=30)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid time range"
            )

        metrics = await metrics_collector.get_slave_metrics(
            slave_id, start_time, end_time
        )

        return {"slave_id": slave_id, "time_range": time_range, "metrics": metrics}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/system", response_model=SystemMetricsResponse)
async def get_system_metrics(
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """获取系统整体监控数据"""
    try:
        # 获取当前时间和24小时前的时间
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)

        # 获取所有从服务器的状态
        slave_metrics = await metrics_collector.get_all_slave_metrics(
            start_time, end_time
        )

        # 获取所有设备的状态
        device_metrics = await metrics_collector.get_all_device_metrics(
            start_time, end_time
        )

        # 计算系统整体指标
        total_slaves = len(slave_metrics)
        healthy_slaves = sum(1 for m in slave_metrics if m["is_healthy"])
        total_devices = len(device_metrics)
        connected_devices = sum(1 for m in device_metrics if m["is_connected"])

        return {
            "total_slaves": total_slaves,
            "healthy_slaves": healthy_slaves,
            "total_devices": total_devices,
            "connected_devices": connected_devices,
            "slave_metrics": slave_metrics,
            "device_metrics": device_metrics,
            "timestamp": end_time.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/cleanup")
async def cleanup_metrics(
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """清理过期的监控数据"""
    try:
        await metrics_collector.cleanup_old_metrics()
        return {"success": True, "message": "Metrics cleanup completed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
