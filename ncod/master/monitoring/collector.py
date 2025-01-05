import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import select
from ..models.device import Device
from ..models.slave import Slave
from ..models.metrics import DeviceMetrics, SlaveMetrics
from ..database import async_session
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Prometheus metrics
device_status = Gauge("ncod_device_status", "Device status", ["device_id", "slave_id"])
device_connection_total = Counter(
    "ncod_device_connection_total", "Total device connections", ["device_id"]
)
device_usage_duration = Histogram(
    "ncod_device_usage_duration", "Device usage duration in seconds", ["device_id"]
)
slave_health = Gauge("ncod_slave_health", "Slave server health status", ["slave_id"])
slave_device_count = Gauge(
    "ncod_slave_device_count", "Number of devices on slave", ["slave_id"]
)


class MetricsCollector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.collection_interval = config.get(
            "metrics_collection_interval", 60
        )  # 默认60秒
        self.retention_days = config.get("metrics_retention_days", 30)  # 默认保留30天
        self.is_running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """启动监控数据收集"""
        if self.is_running:
            return

        self.is_running = True
        self.task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collector started")

    async def stop(self):
        """停止监控数据收集"""
        if not self.is_running:
            return

        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collector stopped")

    async def _collection_loop(self):
        """监控数据收集循环"""
        while self.is_running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(5)  # 发生错误时短暂暂停

    async def _collect_metrics(self):
        """收集所有监控指标"""
        async with async_session() as session:
            # 收集从服务器指标
            slaves = await self._get_active_slaves(session)
            for slave in slaves:
                await self._collect_slave_metrics(session, slave)

            # 收集设备指标
            devices = await self._get_active_devices(session)
            for device in devices:
                await self._collect_device_metrics(session, device)

    async def _get_active_slaves(self, session) -> List[Slave]:
        """获取活跃的从服务器列表"""
        result = await session.execute(select(Slave).where(Slave.is_active == True))
        return result.scalars().all()

    async def _get_active_devices(self, session) -> List[Device]:
        """获取活跃的设备列表"""
        result = await session.execute(select(Device).where(Device.is_active == True))
        return result.scalars().all()

    async def _collect_slave_metrics(self, session, slave: Slave):
        """收集从服务器指标"""
        try:
            # 获取从服务器状态
            is_healthy = await slave.check_health()
            slave_health.labels(slave_id=str(slave.id)).set(1 if is_healthy else 0)

            # 获取设备数量
            device_count = await slave.get_device_count()
            slave_device_count.labels(slave_id=str(slave.id)).set(device_count)

            # 保存到数据库
            metrics = SlaveMetrics(
                slave_id=slave.id,
                timestamp=datetime.now(),
                is_healthy=is_healthy,
                device_count=device_count,
                cpu_usage=await slave.get_cpu_usage(),
                memory_usage=await slave.get_memory_usage(),
                network_tx=await slave.get_network_tx(),
                network_rx=await slave.get_network_rx(),
            )
            session.add(metrics)
            await session.commit()

        except Exception as e:
            logger.error(f"Error collecting metrics for slave {slave.id}: {e}")

    async def _collect_device_metrics(self, session, device: Device):
        """收集设备指标"""
        try:
            # 获取设备状态
            is_connected = await device.is_connected()
            device_status.labels(
                device_id=str(device.id), slave_id=str(device.slave_id)
            ).set(1 if is_connected else 0)

            # 更新连接计数
            if is_connected:
                device_connection_total.labels(device_id=str(device.id)).inc()

            # 获取使用时长
            usage_duration = await device.get_current_usage_duration()
            if usage_duration:
                device_usage_duration.labels(device_id=str(device.id)).observe(
                    usage_duration
                )

            # 保存到数据库
            metrics = DeviceMetrics(
                device_id=device.id,
                timestamp=datetime.now(),
                is_connected=is_connected,
                usage_duration=usage_duration or 0,
                bandwidth_usage=await device.get_bandwidth_usage(),
                error_count=await device.get_error_count(),
            )
            session.add(metrics)
            await session.commit()

        except Exception as e:
            logger.error(f"Error collecting metrics for device {device.id}: {e}")

    async def cleanup_old_metrics(self):
        """清理过期的监控数据"""
        try:
            async with async_session() as session:
                cutoff_date = datetime.now() - timedelta(days=self.retention_days)

                # 清理设备指标
                await session.execute(
                    delete(DeviceMetrics).where(DeviceMetrics.timestamp < cutoff_date)
                )

                # 清理从服务器指标
                await session.execute(
                    delete(SlaveMetrics).where(SlaveMetrics.timestamp < cutoff_date)
                )

                await session.commit()
                logger.info(f"Cleaned up metrics older than {self.retention_days} days")

        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")

    async def get_device_metrics(
        self, device_id: int, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """获取设备监控数据"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(DeviceMetrics)
                    .where(
                        DeviceMetrics.device_id == device_id,
                        DeviceMetrics.timestamp.between(start_time, end_time),
                    )
                    .order_by(DeviceMetrics.timestamp.desc())
                )
                metrics = result.scalars().all()

                return [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "is_connected": m.is_connected,
                        "usage_duration": m.usage_duration,
                        "bandwidth_usage": m.bandwidth_usage,
                        "error_count": m.error_count,
                    }
                    for m in metrics
                ]

        except Exception as e:
            logger.error(f"Error getting device metrics: {e}")
            return []

    async def get_slave_metrics(
        self, slave_id: int, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """获取从服务器监控数据"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(SlaveMetrics)
                    .where(
                        SlaveMetrics.slave_id == slave_id,
                        SlaveMetrics.timestamp.between(start_time, end_time),
                    )
                    .order_by(SlaveMetrics.timestamp.desc())
                )
                metrics = result.scalars().all()

                return [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "is_healthy": m.is_healthy,
                        "device_count": m.device_count,
                        "cpu_usage": m.cpu_usage,
                        "memory_usage": m.memory_usage,
                        "network_tx": m.network_tx,
                        "network_rx": m.network_rx,
                    }
                    for m in metrics
                ]

        except Exception as e:
            logger.error(f"Error getting slave metrics: {e}")
            return []
