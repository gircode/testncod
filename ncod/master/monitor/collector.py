"""监控数据采集器"""

from typing import Dict, Optional
from datetime import datetime
import asyncio
from ncod.core.logger import setup_logger
from ncod.master.services.monitor import MonitorService
from ncod.master.schemas.monitor import MetricsCreate

logger = setup_logger("monitor_collector")


class MetricsCollector:
    """指标采集器"""

    def __init__(self, monitor_service: MonitorService):
        self.monitor_service = monitor_service
        self.running = False

    async def collect_device_metrics(
        self, device_id: str, metrics: Dict
    ) -> Optional[str]:
        """采集设备指标"""
        try:
            metrics_data = MetricsCreate(
                device_id=device_id,
                cpu_usage=metrics.get("cpu", 0.0),
                memory_usage=metrics.get("memory", 0.0),
                disk_usage=metrics.get("disk", 0.0),
                network_io=metrics.get("network", {"rx_bytes": 0, "tx_bytes": 0}),
                timestamp=datetime.utcnow(),
            )
            metrics_record = await self.monitor_service.create_metrics(metrics_data)
            return metrics_record.id
        except Exception as e:
            logger.error(f"Error collecting metrics for device {device_id}: {e}")
            return None

    async def start_collection(self, interval: int = 60):
        """启动采集"""
        self.running = True
        logger.info("Metrics collector started")

    async def stop_collection(self):
        """停止采集"""
        self.running = False
        logger.info("Metrics collector stopped")
