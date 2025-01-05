"""
System Monitoring Module
"""

import asyncio
import logging
import psutil
from datetime import datetime
import aiohttp
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SystemMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.master_url = config["master_url"]
        self.slave_id = config.get("slave_id")
        self.reporting_interval = config.get("reporting_interval", 30)
        self.vh_manager = None  # 将在初始化时设置

    async def start_monitoring(self):
        """启动系统监控"""
        while True:
            try:
                # 收集系统指标
                metrics = self._collect_system_metrics()

                # 获取设备状态
                if self.vh_manager:
                    devices = await self.vh_manager.get_device_list()
                else:
                    devices = []

                # 准备报告数据
                report_data = {
                    "metrics": metrics,
                    "devices": devices,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # 发送到主服务器
                await self._send_report(report_data)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")

            await asyncio.sleep(self.reporting_interval)

    def _collect_system_metrics(self) -> Dict:
        """收集系统指标"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "network": self._get_network_stats(),
        }

    def _get_network_stats(self) -> Dict:
        """获取网络统计信息"""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
        }

    async def _send_report(self, data: Dict):
        """发送报告到主服务器"""
        if not self.slave_id:
            logger.error("Slave ID not set")
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.master_url}/api/v1/slaves/{self.slave_id}/report", json=data
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send report: {response.status}")
                    else:
                        logger.debug("Report sent successfully")
        except Exception as e:
            logger.error(f"Error sending report: {e}")
