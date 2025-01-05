"""从服务器同步客户端"""

import asyncio
import json
from typing import Dict, Optional
from datetime import datetime
import websockets
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.slave.monitor.client import MetricsClient

logger = setup_logger("sync_client")


class SyncClient:
    """同步客户端"""

    def __init__(self):
        self.running = False
        self.ws = None
        self.metrics_client = MetricsClient()
        self.master_ws_url = f"ws://{config.master_host}:{config.master_port}/ws"

    async def connect(self) -> bool:
        """连接到主服务器"""
        try:
            self.ws = await websockets.connect(self.master_ws_url)
            logger.info("Connected to master server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to master server: {e}")
            return False

    async def send_metrics(self, metrics: Dict) -> bool:
        """发送指标数据"""
        if not self.ws:
            return False
        try:
            message = {
                "type": "metrics",
                "data": metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self.ws.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending metrics: {e}")
            return False

    async def start(self):
        """启动同步"""
        self.running = True
        while self.running:
            try:
                if not self.ws:
                    if not await self.connect():
                        await asyncio.sleep(5)
                        continue

                # 启动指标采集
                metrics = self.metrics_client.get_system_metrics()
                if metrics:
                    await self.send_metrics(metrics)

                await asyncio.sleep(config.metrics_interval)
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                self.ws = None
                await asyncio.sleep(5)

    async def stop(self):
        """停止同步"""
        self.running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
        logger.info("Sync client stopped")
