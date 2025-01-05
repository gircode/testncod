import asyncio
import json
import logging
from typing import Optional, Callable
import websockets
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketClient:
    def __init__(self, url: str, device_manager, slave_id: int):
        self.url = url
        self.device_manager = device_manager
        self.slave_id = slave_id
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.reconnect_interval = 5
        self.is_connected = False

    async def connect(self):
        """连接到主服务器"""
        while True:
            try:
                async with websockets.connect(self.url) as websocket:
                    self.ws = websocket
                    self.is_connected = True
                    logger.info("Connected to master server")

                    # 注册从服务器
                    await self.register_slave()

                    # 开始接收消息
                    await self.receive_messages()

            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                self.is_connected = False
                await asyncio.sleep(self.reconnect_interval)

    async def register_slave(self):
        """注册从服务器"""
        await self.send_message({"type": "register_slave", "slave_id": self.slave_id})

    async def send_message(self, message: dict):
        """发送消息到主服务器"""
        if self.ws and self.is_connected:
            try:
                await self.ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                self.is_connected = False

    async def receive_messages(self):
        """接收并处理主服务器的消息"""
        try:
            while True:
                message = await self.ws.recv()
                data = json.loads(message)
                await self.handle_message(data)
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            self.is_connected = False

    async def handle_message(self, data: dict):
        """处理接收到的消息"""
        try:
            message_type = data.get("type")

            if message_type == "connect_device":
                device_id = data["device_id"]
                user_id = data["user_id"]
                success = await self.device_manager.connect_device(device_id, user_id)
                await self.send_status_update(
                    device_id, "connected" if success else "error"
                )

            elif message_type == "disconnect_device":
                device_id = data["device_id"]
                success = await self.device_manager.disconnect_device(device_id)
                await self.send_status_update(
                    device_id, "online" if success else "error"
                )

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def send_status_update(self, device_id: int, status: str):
        """发送设备状态更新"""
        await self.send_message(
            {
                "type": "status_update",
                "device_id": device_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def start_status_reporting(self):
        """开始定期报告设备状态"""
        while True:
            if self.is_connected:
                for device_id, device in self.device_manager.devices.items():
                    await self.send_status_update(device_id, device["status"])
            await asyncio.sleep(30)  # 每30秒报告一次
