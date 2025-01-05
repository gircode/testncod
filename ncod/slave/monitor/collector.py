"""监控数据采集器"""

import asyncio
import psutil
from typing import Dict, Optional
from datetime import datetime
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.slave.device.manager import device_manager

logger = setup_logger("monitor_collector")


class MetricsCollector:
    """指标采集器"""

    def __init__(self):
        self.running = False
        self.metrics: Dict[str, Dict] = {}
        self.last_collection: Optional[datetime] = None

    async def start(self):
        """启动采集器"""
        try:
            self.running = True
            asyncio.create_task(self._collection_loop())
            logger.info("Metrics collector started")
        except Exception as e:
            logger.error(f"Error starting metrics collector: {e}")
            raise

    async def stop(self):
        """停止采集器"""
        try:
            self.running = False
            logger.info("Metrics collector stopped")
        except Exception as e:
            logger.error(f"Error stopping metrics collector: {e}")

    async def _collection_loop(self):
        """采集循环"""
        while self.running:
            try:
                await self.collect_metrics()
                await asyncio.sleep(config.metrics_interval)
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(5)

    async def collect_metrics(self):
        """采集指标"""
        try:
            # 系统指标
            system_metrics = {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "network": self._get_network_metrics(),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # 设备指标
            device_metrics = {
                "total_devices": len(device_manager.controller.devices),
                "active_devices": len(
                    [
                        d
                        for d in device_manager.controller.devices.values()
                        if d["status"] == "in_use"
                    ]
                ),
                "device_statuses": self._get_device_statuses(),
            }

            # 更新指标
            self.metrics.update({"system": system_metrics, "devices": device_metrics})
            self.last_collection = datetime.utcnow()

            logger.debug("Metrics collected successfully")
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

    def _get_network_metrics(self) -> Dict:
        """获取网络指标"""
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout,
            }
        except Exception as e:
            logger.error(f"Error getting network metrics: {e}")
            return {}

    def _get_device_statuses(self) -> Dict:
        """获取设备状态统计"""
        try:
            status_count = {}
            for device in device_manager.controller.devices.values():
                status = device["status"]
                status_count[status] = status_count.get(status, 0) + 1
            return status_count
        except Exception as e:
            logger.error(f"Error getting device statuses: {e}")
            return {}

    def get_current_metrics(self) -> Dict:
        """获取当前指标"""
        return self.metrics.copy()

    def get_device_metrics(self, device_id: str) -> Optional[Dict]:
        """获取特定设备的指标"""
        try:
            device = device_manager.controller.devices.get(device_id)
            if device:
                usage = device_manager.get_device_usage(device_id)
                return {
                    "status": device["status"],
                    "last_seen": device["last_seen"].isoformat(),
                    "total_usage_time": usage.get("total_time", 0) if usage else 0,
                    "session_count": usage.get("session_count", 0) if usage else 0,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting device metrics for {device_id}: {e}")
            return None


# 创建全局指标采集器实例
metrics_collector = MetricsCollector()
