"""监控服务模块"""

from typing import Dict
import psutil
from prometheus_client import Gauge

from ncod.core.config import settings
from ncod.utils.logger import logger


class MonitorService:
    """监控服务"""

    def __init__(self):
        # Prometheus指标
        self.metrics = {
            "cpu_usage": Gauge("slave_cpu_usage_percent", "从节点CPU使用率"),
            "memory_usage": Gauge("slave_memory_usage_percent", "从节点内存使用率"),
            "disk_usage": Gauge("slave_disk_usage_percent", "从节点磁盘使用率"),
        }

    async def collect_metrics(self) -> Dict[str, float]:
        """收集系统指标"""
        try:
            # 基础系统指标
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "disk_percent": disk.percent,
                "disk_free": disk.free,
            }

            # 更新Prometheus指标
            self.metrics["cpu_usage"].set(cpu_percent)
            self.metrics["memory_usage"].set(memory.percent)
            self.metrics["disk_usage"].set(disk.percent)

            return metrics

        except Exception as e:
            logger.error(f"收集系统指标失败: {str(e)}")
            return {}

    async def check_alerts(self) -> list[Dict[str, str]]:
        """检查告警"""
        alerts = []

        try:
            metrics = await self.collect_metrics()

            # CPU使用率告警
            if metrics.get("cpu_percent", 0) > settings.ALERT_CPU_THRESHOLD:
                alerts.append(
                    {
                        "type": "cpu",
                        "level": "critical",
                        "message": f"CPU使用率超过{settings.ALERT_CPU_THRESHOLD}%",
                    }
                )

            # 内存使用率告警
            if metrics.get("memory_percent", 0) > settings.ALERT_MEMORY_THRESHOLD:
                alerts.append(
                    {
                        "type": "memory",
                        "level": "critical",
                        "message": f"内存使用率超过{settings.ALERT_MEMORY_THRESHOLD}%",
                    }
                )

            # 磁盘使用率告警
            if metrics.get("disk_percent", 0) > settings.ALERT_DISK_THRESHOLD:
                alerts.append(
                    {
                        "type": "disk",
                        "level": "critical",
                        "message": f"磁盘使用率超过{settings.ALERT_DISK_THRESHOLD}%",
                    }
                )

            return alerts

        except Exception as e:
            logger.error(f"检查系统告警失败: {str(e)}")
            return []


monitor_service = MonitorService()
