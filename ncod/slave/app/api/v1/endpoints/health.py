"""
健康检查端点
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.session import get_db
from ....services.health import HealthService

router = APIRouter()


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """健康检查"""
    health_service = HealthService(db)
    return await health_service.check()


@router.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """获取状态"""
    health_service = HealthService(db)
    return await health_service.get_status()


@router.get("/metrics")
async def get_health_metrics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """获取健康指标"""
    health_service = HealthService(db)
    return await health_service.get_metrics()


@router.get("/alerts")
async def get_health_alerts(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """获取健康告警"""
    health_service = HealthService(db)
    return await health_service.get_alerts()
