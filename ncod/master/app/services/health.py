"""
健康检查服务
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
import psutil
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.auth import SlaveServer

# 配置日志
logger = logging.getLogger(__name__)


class HealthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check(self) -> Dict:
        """检查系统健康状态"""
        try:
            # 检查CPU使用率
            cpu_status = await self._check_cpu()

            # 检查内存使用率
            memory_status = await self._check_memory()

            # 检查磁盘使用率
            disk_status = await self._check_disk()

            # 检查数据库连接
            db_status = await self._check_database()

            # 检查从服务器状态
            slave_status = await self._check_slaves()

            # 汇总状态
            status = {
                "healthy": all(
                    [
                        cpu_status["healthy"],
                        memory_status["healthy"],
                        disk_status["healthy"],
                        db_status["healthy"],
                        slave_status["healthy"],
                    ]
                ),
                "timestamp": datetime.utcnow(),
                "components": {
                    "cpu": cpu_status,
                    "memory": memory_status,
                    "disk": disk_status,
                    "database": db_status,
                    "slaves": slave_status,
                },
            }

            return status

        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {"healthy": False, "timestamp": datetime.utcnow(), "error": str(e)}

    async def _check_cpu(self) -> Dict:
        """检查CPU状态"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            return {
                "healthy": cpu_percent < settings.CPU_ALERT_THRESHOLD,
                "usage_percent": cpu_percent,
                "core_count": cpu_count,
                "frequency": {
                    "current": cpu_freq.current if cpu_freq else None,
                    "min": cpu_freq.min if cpu_freq else None,
                    "max": cpu_freq.max if cpu_freq else None,
                },
            }

        except Exception as e:
            logger.error(f"CPU状态检查失败: {str(e)}")
            return {"healthy": False, "error": str(e)}

    async def _check_memory(self) -> Dict:
        """检查内存状态"""
        try:
            memory = psutil.virtual_memory()

            return {
                "healthy": memory.percent < settings.MEMORY_ALERT_THRESHOLD,
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "usage_percent": memory.percent,
            }

        except Exception as e:
            logger.error(f"内存状态检查失败: {str(e)}")
            return {"healthy": False, "error": str(e)}

    async def _check_disk(self) -> Dict:
        """检查磁盘状态"""
        try:
            disk = psutil.disk_usage("/")

            return {
                "healthy": disk.percent < settings.DISK_ALERT_THRESHOLD,
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "usage_percent": disk.percent,
            }

        except Exception as e:
            logger.error(f"磁盘状态检查失败: {str(e)}")
            return {"healthy": False, "error": str(e)}

    async def _check_database(self) -> Dict:
        """检查数据库状态"""
        try:
            # 执行简单查询测试数据库连接
            await self.db.execute(select(1))

            return {"healthy": True, "connected": True}

        except Exception as e:
            logger.error(f"数据库状态检查失败: {str(e)}")
            return {"healthy": False, "connected": False, "error": str(e)}

    async def _check_slaves(self) -> Dict:
        """检查从服务器状态"""
        try:
            # 获取所有从服务器
            result = await self.db.execute(select(SlaveServer))
            slaves = result.scalars().all()

            slave_status = []
            all_healthy = True

            for slave in slaves:
                if not slave.is_active:
                    continue

                status = {
                    "id": slave.id,
                    "name": slave.name,
                    "host": slave.host,
                    "port": slave.port,
                }

                try:
                    # 检查从服务器健康状态
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"http://{slave.host}:{slave.port}/health", timeout=5
                        ) as response:
                            if response.status != 200:
                                status.update(
                                    {
                                        "healthy": False,
                                        "error": f"HTTP {response.status}",
                                    }
                                )
                                all_healthy = False
                                continue

                            data = await response.json()
                            status.update(
                                {"healthy": data.get("healthy", False), "details": data}
                            )

                            if not data.get("healthy", False):
                                all_healthy = False

                except Exception as e:
                    status.update({"healthy": False, "error": str(e)})
                    all_healthy = False

                slave_status.append(status)

            return {
                "healthy": all_healthy,
                "total_count": len(slaves),
                "active_count": len(slave_status),
                "slaves": slave_status,
            }

        except Exception as e:
            logger.error(f"从服务器状态检查失败: {str(e)}")
            return {"healthy": False, "error": str(e)}

    async def get_system_summary(self) -> Dict:
        """获取系统概要信息"""
        try:
            # 获取基本系统信息
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            boot_time = datetime.fromtimestamp(psutil.boot_time())

            # 获取从服务器信息
            result = await self.db.execute(
                select(SlaveServer).where(SlaveServer.is_active == True)
            )
            active_slaves = result.scalars().all()

            # 获取最近的健康状态
            health_status = await self.check()

            return {
                "system": {
                    "cpu": {
                        "count": cpu_count,
                        "frequency": {
                            "current": cpu_freq.current if cpu_freq else None,
                            "min": cpu_freq.min if cpu_freq else None,
                            "max": cpu_freq.max if cpu_freq else None,
                        },
                    },
                    "memory": {"total": memory.total, "available": memory.available},
                    "disk": {"total": disk.total, "free": disk.free},
                    "boot_time": boot_time,
                    "uptime": datetime.utcnow() - boot_time,
                },
                "slaves": {
                    "total": len(active_slaves),
                    "list": [
                        {
                            "id": slave.id,
                            "name": slave.name,
                            "host": slave.host,
                            "port": slave.port,
                            "last_heartbeat": slave.last_heartbeat,
                        }
                        for slave in active_slaves
                    ],
                },
                "health_status": health_status,
            }

        except Exception as e:
            logger.error(f"获取系统概要信息失败: {str(e)}")
            return {"error": str(e)}
