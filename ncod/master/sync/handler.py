"""主服务器同步处理器"""

from typing import Dict, Optional
from datetime import datetime
from ncod.core.logger import setup_logger
from ncod.master.services.monitor import MonitorService
from ncod.master.monitor.collector import MetricsCollector

logger = setup_logger("sync_handler")


class SyncHandler:
    """同步处理器"""

    def __init__(self):
        self.monitor_service = MonitorService()
        self.metrics_collector = MetricsCollector(self.monitor_service)

    async def handle_metrics(self, slave_id: str, metrics: Dict) -> Optional[str]:
        """处理指标数据"""
        try:
            # 记录设备指标
            if "device_id" in metrics:
                return await self.metrics_collector.collect_device_metrics(
                    metrics["device_id"], metrics
                )
            return None
        except Exception as e:
            logger.error(f"Error handling metrics from slave {slave_id}: {e}")
            return None

    async def handle_device_status(self, slave_id: str, status: Dict) -> bool:
        """处理设备状态"""
        try:
            # 这里添加设备状态更新逻辑
            logger.info(f"Received device status from slave {slave_id}: {status}")
            return True
        except Exception as e:
            logger.error(f"Error handling device status from slave {slave_id}: {e}")
            return False
