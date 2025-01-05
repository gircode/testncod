"""监控客户端"""

import asyncio
import json
from typing import Dict, Optional
from datetime import datetime
import aiohttp
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.slave.monitor.collector import metrics_collector

logger = setup_logger("monitor_client")


class MonitorClient:
    """监控客户端"""

    def __init__(self):
        self.collector = metrics_collector
        self.running = False
        self.master_url = config.master_url
        self.node_id = config.slave_id

    async def start(self):
        """启动客户端"""
        try:
            self.running = True
            await self.collector.start()
            asyncio.create_task(self._reporting_loop())
            logger.info("Monitor client started")
        except Exception as e:
            logger.error(f"Error starting monitor client: {e}")
            raise

    async def stop(self):
        """停止客户端"""
        try:
            self.running = False
            await self.collector.stop()
            logger.info("Monitor client stopped")
        except Exception as e:
            logger.error(f"Error stopping monitor client: {e}")

    async def _reporting_loop(self):
        """报告循环"""
        while self.running:
            try:
                await self.report_metrics()
                await asyncio.sleep(config.reporting_interval)
            except Exception as e:
                logger.error(f"Error in reporting loop: {e}")
                await asyncio.sleep(5)

    async def report_metrics(self):
        """报告指标"""
        try:
            metrics = self.collector.get_current_metrics()
            if not metrics:
                return

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.master_url}/api/v1/monitor/metrics",
                    json={
                        "node_id": self.node_id,
                        "metrics": metrics,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                ) as response:
                    if response.status != 200:
                        logger.error(
                            f"Error reporting metrics: {await response.text()}"
                        )
                    else:
                        logger.debug("Metrics reported successfully")
        except Exception as e:
            logger.error(f"Error reporting metrics: {e}")


# 创建全局监控客户端实例
monitor_client = MonitorClient()
