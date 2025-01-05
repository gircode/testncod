"""系统监控API端点"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from ncod.core.monitor import SystemMonitor
from ncod.core.db.base import get_db
from ncod.middleware.auth import get_current_user
from ncod.utils.logger import logger

router = APIRouter()
system_monitor = SystemMonitor()


@router.get("/system")
async def get_system_stats(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """获取系统状态"""
    try:
        return system_monitor.get_system_stats()
    except Exception as e:
        logger.error("获取系统状态失败", exc_info=True)
        raise


@router.get("/process")
async def get_process_stats(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """获取进程状态"""
    try:
        return system_monitor.get_process_stats()
    except Exception as e:
        logger.error("获取进程状态失败", exc_info=True)
        raise


@router.get("/health")
async def check_health(db: AsyncSession = Depends(get_db)) -> Dict[str, bool]:
    """检查系统健康状态"""
    try:
        db_health = await system_monitor.check_database_health(db)
        return {"database": db_health, "system": True}
    except Exception as e:
        logger.error("健康检查失败", exc_info=True)
        return {"database": False, "system": False}
