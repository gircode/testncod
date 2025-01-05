"""健康检查服务"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict
import psutil
from fastapi_cache2.decorator import cache
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.monitor import MonitorAlert, MonitorMetric
from .monitor import monitor_service

logger = logging.getLogger(__name__)


class HealthService:
    """健康检查服务"""

    def __init__(self, db: AsyncSession):
        """初始化健康检查服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.metrics_page_size = 100
        self.cache_ttl = 60

    @cache(expire=60)
    async def check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
        }

        # 系统检查
        cpu_status = self._check_cpu()
        status["checks"]["cpu"] = cpu_status
        if cpu_status["status"] != "healthy":
            status["status"] = "unhealthy"

        memory_status = self._check_memory()
        status["checks"]["memory"] = memory_status
        if memory_status["status"] != "healthy":
            status["status"] = "unhealthy"

        disk_status = self._check_disk()
        status["checks"]["disk"] = disk_status
        if disk_status["status"] != "healthy":
            status["status"] = "unhealthy"

        # 数据库检查
        db_status = await self._check_database()
        status["checks"]["database"] = db_status
        if db_status["status"] != "healthy":
            status["status"] = "unhealthy"

        return status

    def _check_cpu(self) -> Dict[str, Any]:
        """检查CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            return {
                "status": (
                    "healthy" if cpu_percent < settings.CPU_THRESHOLD else "warning"
                ),
                "usage": cpu_percent,
                "threshold": settings.CPU_THRESHOLD,
            }
        except Exception as e:
            logger.error(f"CPU检查失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _check_memory(self) -> Dict[str, Any]:
        """检查内存"""
        try:
            memory = psutil.virtual_memory()
            return {
                "status": (
                    "healthy"
                    if memory.percent < settings.MEMORY_THRESHOLD
                    else "warning"
                ),
                "usage": memory.percent,
                "available": memory.available,
                "total": memory.total,
                "threshold": settings.MEMORY_THRESHOLD,
            }
        except Exception as e:
            logger.error(f"内存检查失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _check_disk(self) -> Dict[str, Any]:
        """检查磁盘"""
        try:
            disk = psutil.disk_usage("/")
            return {
                "status": (
                    "healthy" if disk.percent < settings.DISK_THRESHOLD else "warning"
                ),
                "usage": disk.percent,
                "free": disk.free,
                "total": disk.total,
                "threshold": settings.DISK_THRESHOLD,
            }
        except Exception as e:
            logger.error(f"磁盘检查失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _check_database(self) -> Dict[str, Any]:
        """检查数据库"""
        try:
            start_time = datetime.utcnow()
            await self.db.execute(select(func.now()))
            end_time = datetime.utcnow()

            latency = (end_time - start_time).total_seconds() * 1000

            return {
                "status": "healthy" if latency < 1000 else "warning",
                "latency": latency,
            }
        except Exception as e:
            logger.error(f"数据库检查失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    @cache(expire=300)
    async def get_system_summary(self) -> Dict[str, Any]:
        """获取系统概况"""
        try:
            # 获取告警统计
            alerts_result = await self.db.execute(
                select(
                    func.count().label("total"),
                    func.sum(
                        case((MonitorAlert.severity == "critical", 1), else_=0)
                    ).label("critical"),
                    func.sum(
                        case((MonitorAlert.severity == "warning", 1), else_=0)
                    ).label("warning"),
                )
                .select_from(MonitorAlert)
                .where(MonitorAlert.status == "active")
            )
            alerts_stats = alerts_result.first()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "alerts": {
                    "total": alerts_stats.total or 0,
                    "critical": alerts_stats.critical or 0,
                    "warning": alerts_stats.warning or 0,
                },
                "system": {
                    "cpu": self._check_cpu(),
                    "memory": self._check_memory(),
                    "disk": self._check_disk(),
                },
            }

        except Exception as e:
            logger.error(f"获取系统概况失败: {str(e)}")
            return {"timestamp": datetime.utcnow().isoformat(), "error": str(e)}

    @cache(expire=60)
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            metrics = await monitor_service.collect_metrics()
            alerts = await monitor_service.check_alerts()

            return {
                "status": "healthy" if not alerts else "warning",
                "metrics": metrics,
                "alerts": alerts,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    @cache(expire=300)
    async def get_alert_summary(self) -> Dict[str, Any]:
        """获取告警摘要"""
        try:
            # 获取最近24小时的告警统计
            start_time = datetime.now() - timedelta(hours=24)

            result = await session.execute(
                select(
                    func.count().label("total"),
                    func.sum(
                        case((MonitorAlert.severity == "critical", 1), else_=0)
                    ).label("critical"),
                    func.sum(
                        case((MonitorAlert.severity == "warning", 1), else_=0)
                    ).label("warning"),
                ).where(MonitorAlert.created_at >= start_time)
            )

            stats = result.first()

            return {
                "total": stats.total or 0,
                "critical": stats.critical or 0,
                "warning": stats.warning or 0,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取告警摘要失败: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


health_service = HealthService()
