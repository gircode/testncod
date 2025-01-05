"""性能监控服务"""

import asyncio
import psutil
import platform
from datetime import datetime
from typing import Dict, List, Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ncod.master.models.device import Device
from ncod.master.core.database import async_session
from ncod.utils.logger import logger
from ncod.utils.cache import redis_cache
from ncod.utils.config import settings


class PerformanceMonitor:
    """性能监控服务"""

    def __init__(self):
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._metrics: Dict[str, Dict] = {}  # 性能指标
        self._alerts: Dict[str, Dict] = {}  # 告警信息

    async def start(self):
        """启动监控服务"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("性能监控服务已启动")

    async def stop(self):
        """停止监控服务"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("性能监控服务已停止")

    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                await self._collect_metrics()
                await self._analyze_metrics()
                await self._check_alerts()
                await asyncio.sleep(settings.PERF_CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"性能监控失败: {e}")
                await asyncio.sleep(5)  # 出错后等待5秒再重试

    async def _collect_metrics(self):
        """收集性能指标"""
        try:
            # 收集系统性能指标
            system_metrics = await self._collect_system_metrics()
            self._metrics["system"] = system_metrics

            # 收集设备性能指标
            async with async_session() as session:
                result = await session.execute(select(Device))
                devices = result.scalars().all()

                for device in devices:
                    device_metrics = await self._collect_device_metrics(device)
                    self._metrics[f"device:{device.id}"] = device_metrics

            # 缓存性能指标
            await redis_cache.set(
                "performance_metrics", self._metrics, expire=settings.PERF_CACHE_TTL
            )

        except Exception as e:
            logger.error(f"收集性能指标失败: {e}")

    async def _collect_system_metrics(self) -> Dict:
        """收集系统性能指标

        Returns:
            Dict: 系统性能指标
        """
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": psutil.cpu_percent(interval=1),
                    "count": psutil.cpu_count(),
                    "freq": psutil.cpu_freq()._asdict(),
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                },
                "disk": {
                    "total": psutil.disk_usage("/").total,
                    "used": psutil.disk_usage("/").used,
                    "free": psutil.disk_usage("/").free,
                    "percent": psutil.disk_usage("/").percent,
                },
                "network": {
                    "bytes_sent": psutil.net_io_counters().bytes_sent,
                    "bytes_recv": psutil.net_io_counters().bytes_recv,
                    "packets_sent": psutil.net_io_counters().packets_sent,
                    "packets_recv": psutil.net_io_counters().packets_recv,
                    "errin": psutil.net_io_counters().errin,
                    "errout": psutil.net_io_counters().errout,
                    "dropin": psutil.net_io_counters().dropin,
                    "dropout": psutil.net_io_counters().dropout,
                },
                "system": {
                    "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "processes": len(psutil.pids()),
                },
            }

            return metrics

        except Exception as e:
            logger.error(f"收集系统性能指标失败: {e}")
            return {}

    async def _collect_device_metrics(self, device: Device) -> Dict:
        """收集设备性能指标

        Args:
            device: 设备实例

        Returns:
            Dict: 设备性能指标
        """
        try:
            # 从缓存获取设备性能指标
            cache_key = f"device_metrics:{device.id}"
            metrics = await redis_cache.get(cache_key)

            if metrics:
                return metrics

            # 收集设备性能指标
            # TODO: 实现具体的设备性能指标收集逻辑
            # 可以考虑:
            # 1. USB带宽使用率
            # 2. 设备响应时间
            # 3. 错误计数
            # 4. 重连次数
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "status": device.status.value,
                "bandwidth": {"in": 0, "out": 0},
                "latency": 0,
                "errors": 0,
                "reconnects": 0,
            }

            # 缓存设备性能指标
            await redis_cache.set(cache_key, metrics, expire=settings.PERF_CACHE_TTL)

            return metrics

        except Exception as e:
            logger.error(f"收集设备性能指标失败: {e}")
            return {}

    async def _analyze_metrics(self):
        """分析性能指标"""
        try:
            # 分析系统性能
            if "system" in self._metrics:
                await self._analyze_system_metrics(self._metrics["system"])

            # 分析设备性能
            for key, metrics in self._metrics.items():
                if key.startswith("device:"):
                    device_id = key.split(":", 1)[1]
                    await self._analyze_device_metrics(device_id, metrics)

        except Exception as e:
            logger.error(f"分析性能指标失败: {e}")

    async def _analyze_system_metrics(self, metrics: Dict):
        """分析系统性能指标

        Args:
            metrics: 系统性能指标
        """
        try:
            # 检查CPU使用率
            if metrics["cpu"]["percent"] > settings.PERF_CPU_THRESHOLD:
                await self._add_alert(
                    "system", "cpu_high", f"CPU使用率过高: {metrics['cpu']['percent']}%"
                )

            # 检查内存使用率
            if metrics["memory"]["percent"] > settings.PERF_MEMORY_THRESHOLD:
                await self._add_alert(
                    "system",
                    "memory_high",
                    f"内存使用率过高: {metrics['memory']['percent']}%",
                )

            # 检查磁盘使用率
            if metrics["disk"]["percent"] > settings.PERF_DISK_THRESHOLD:
                await self._add_alert(
                    "system",
                    "disk_high",
                    f"磁盘使用率过高: {metrics['disk']['percent']}%",
                )

            # 检查网络错误
            network = metrics["network"]
            if network["errin"] > 0 or network["errout"] > 0:
                await self._add_alert(
                    "system",
                    "network_error",
                    f"网络错误: 接收{network['errin']},发送{network['errout']}",
                )

        except Exception as e:
            logger.error(f"分析系统性能指标失败: {e}")

    async def _analyze_device_metrics(self, device_id: str, metrics: Dict):
        """分析设备性能指标

        Args:
            device_id: 设备ID
            metrics: 设备性能指标
        """
        try:
            # 检查设备状态
            if metrics["status"] == "error":
                await self._add_alert(
                    f"device:{device_id}", "device_error", f"设备状态异常: {device_id}"
                )

            # 检查设备延迟
            if metrics["latency"] > settings.PERF_LATENCY_THRESHOLD:
                await self._add_alert(
                    f"device:{device_id}",
                    "latency_high",
                    f"设备延迟过高: {metrics['latency']}ms",
                )

            # 检查错误计数
            if metrics["errors"] > settings.PERF_ERROR_THRESHOLD:
                await self._add_alert(
                    f"device:{device_id}",
                    "error_high",
                    f"设备错误过多: {metrics['errors']}",
                )

            # 检查重连次数
            if metrics["reconnects"] > settings.PERF_RECONNECT_THRESHOLD:
                await self._add_alert(
                    f"device:{device_id}",
                    "reconnect_high",
                    f"设备重连过于频繁: {metrics['reconnects']}",
                )

        except Exception as e:
            logger.error(f"分析设备性能指标失败: {e}")

    async def _add_alert(self, source: str, alert_type: str, message: str):
        """添加告警

        Args:
            source: 告警源
            alert_type: 告警类型
            message: 告警消息
        """
        try:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "type": alert_type,
                "message": message,
            }

            # 更新告警信息
            self._alerts[f"{source}:{alert_type}"] = alert

            # 发送告警通知
            await redis_cache.publish("performance_alert", alert)

            logger.warning(f"性能告警: {message}")

        except Exception as e:
            logger.error(f"添加告警失败: {e}")

    async def _check_alerts(self):
        """检查告警状态"""
        try:
            current_time = datetime.now()
            expired_alerts = []

            # 检查告警是否过期
            for key, alert in self._alerts.items():
                alert_time = datetime.fromisoformat(alert["timestamp"])
                if (current_time - alert_time).seconds > settings.ALERT_EXPIRE_TIME:
                    expired_alerts.append(key)

            # 删除过期告警
            for key in expired_alerts:
                self._alerts.pop(key, None)

        except Exception as e:
            logger.error(f"检查告警状态失败: {e}")

    def get_metrics(self) -> Dict:
        """获取性能指标

        Returns:
            Dict: 性能指标
        """
        return self._metrics.copy()

    def get_alerts(self) -> Dict:
        """获取告警信息

        Returns:
            Dict: 告警信息
        """
        return self._alerts.copy()

    async def get_device_metrics(self, device_id: str) -> Optional[Dict]:
        """获取设备性能指标

        Args:
            device_id: 设备ID

        Returns:
            Optional[Dict]: 设备性能指标
        """
        try:
            key = f"device:{device_id}"
            if key in self._metrics:
                return self._metrics[key]

            # 从缓存获取
            cache_key = f"device_metrics:{device_id}"
            return await redis_cache.get(cache_key)

        except Exception as e:
            logger.error(f"获取设备性能指标失败: {e}")
            return None

    async def get_system_metrics(self) -> Optional[Dict]:
        """获取系统性能指标

        Returns:
            Optional[Dict]: 系统性能指标
        """
        try:
            if "system" in self._metrics:
                return self._metrics["system"]

            # 从缓存获取
            return await redis_cache.get("system_metrics")

        except Exception as e:
            logger.error(f"获取系统性能指标失败: {e}")
            return None


# 创建全局性能监控实例
performance_monitor = PerformanceMonitor()
