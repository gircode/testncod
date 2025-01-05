"""主服务器核心模块"""

import asyncio
from typing import Optional
from fastapi import FastAPI
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.master.websocket.server import WebSocketServer
from ncod.master.monitor.collector import MetricsCollector
from ncod.master.services.monitor import MonitorService

logger = setup_logger("master_server")


class MasterServer:
    """主服务器"""

    def __init__(self):
        self.app = FastAPI(title="NCOD Master Server")
        self.ws_server = WebSocketServer()
        self.monitor_service = MonitorService()
        self.metrics_collector = MetricsCollector(self.monitor_service)
        self.running = False

    async def start(self):
        """启动服务器"""
        try:
            self.running = True
            logger.info("Master server starting...")

            # 启动指标采集器
            await self.metrics_collector.start_collection(
                interval=config.metrics_interval
            )

            logger.info("Master server started")
        except Exception as e:
            logger.error(f"Error starting master server: {e}")
            self.running = False
            raise

    async def stop(self):
        """停止服务器"""
        try:
            self.running = False
            logger.info("Master server stopping...")

            # 停止指标采集器
            await self.metrics_collector.stop_collection()

            logger.info("Master server stopped")
        except Exception as e:
            logger.error(f"Error stopping master server: {e}")
            raise

    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app
