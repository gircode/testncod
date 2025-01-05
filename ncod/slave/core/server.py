"""从服务器核心模块"""

import asyncio
from typing import Optional
from fastapi import FastAPI
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.slave.monitor.client import MetricsClient
from ncod.slave.sync.client import SyncClient
from ncod.slave.device.manager import DeviceManager

logger = setup_logger("slave_server")


class SlaveServer:
    """从服务器"""

    def __init__(self):
        self.app = FastAPI(title="NCOD Slave Server")
        self.metrics_client = MetricsClient()
        self.sync_client = SyncClient()
        self.device_manager = DeviceManager()
        self.running = False

    async def start(self):
        """启动服务器"""
        try:
            self.running = True
            logger.info("Slave server starting...")

            # 启动设备管理器
            await self.device_manager.start()

            # 启动指标采集
            asyncio.create_task(self.metrics_client.start_reporting())

            # 启动同步客户端
            asyncio.create_task(self.sync_client.start())

            logger.info("Slave server started")
        except Exception as e:
            logger.error(f"Error starting slave server: {e}")
            self.running = False
            raise

    async def stop(self):
        """停止服务器"""
        try:
            self.running = False
            logger.info("Slave server stopping...")

            # 停止设备管理器
            await self.device_manager.stop()

            # 停止指标采集
            await self.metrics_client.stop_reporting()

            # 停止同步客户端
            await self.sync_client.stop()

            logger.info("Slave server stopped")
        except Exception as e:
            logger.error(f"Error stopping slave server: {e}")
            raise

    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app
