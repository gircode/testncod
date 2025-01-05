"""WebSocket消息处理器"""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import WebSocket
from ncod.core.logger import master_logger as logger
from ncod.master.services.device import DeviceService
from ncod.master.services.monitor import MonitorService
from ncod.master.services.slave import SlaveService


class WebSocketHandler:
    def __init__(self, ws_server):
        self.ws_server = ws_server
        self.device_service = DeviceService()
        self.monitor_service = MonitorService()
        self.slave_service = SlaveService()

    async def handle_client_message(self, client_id: str, message: Dict[str, Any]):
        """处理客户端消息"""
        try:
            message_type = message.get("type")
            if message_type == "subscribe_device":
                await self._handle_device_subscription(client_id, message)
            elif message_type == "device_command":
                await self._handle_device_command(client_id, message)
            else:
                logger.warning(f"Unknown message type from client: {message_type}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    async def handle_slave_message(self, slave_id: str, message: Dict[str, Any]):
        """处理从服务器消息"""
        try:
            message_type = message.get("type")
            if message_type == "device_status":
                await self._handle_device_status(slave_id, message)
            elif message_type == "metrics":
                await self._handle_metrics(slave_id, message)
            elif message_type == "heartbeat":
                await self._handle_heartbeat(slave_id, message)
            else:
                logger.warning(f"Unknown message type from slave: {message_type}")
        except Exception as e:
            logger.error(f"Error handling slave message: {e}")

    async def _handle_device_subscription(
        self, client_id: str, message: Dict[str, Any]
    ):
        """处理设备订阅"""
        device_id = message.get("device_id")
        action = message.get("action")

        if action == "subscribe":
            await self.ws_server.subscribe_device(client_id, device_id)
        elif action == "unsubscribe":
            await self.ws_server.unsubscribe_device(client_id, device_id)

    async def _handle_device_command(self, client_id: str, message: Dict[str, Any]):
        """处理设备命令"""
        device_id = message.get("device_id")
        command = message.get("command")
        params = message.get("params", {})

        try:
            result = await self.device_service.execute_device_command(
                device_id, command, params
            )
            await self.ws_server.broadcast_device_status(device_id, result)
        except Exception as e:
            logger.error(f"Error executing device command: {e}")
            # 发送错误响应给客户端
            await self.ws_server.broadcast(
                {"type": "error", "device_id": device_id, "error": str(e)}
            )

    async def _handle_device_status(self, slave_id: str, message: Dict[str, Any]):
        """处理设备状态更新"""
        device_id = message.get("device_id")
        status = message.get("status")

        try:
            # 更新设备状态
            await self.device_service.update_device_status(device_id, status)
            # 广播状态更新
            await self.ws_server.broadcast_device_status(device_id, status)
        except Exception as e:
            logger.error(f"Error handling device status: {e}")

    async def _handle_metrics(self, slave_id: str, message: Dict[str, Any]):
        """处理监控指标"""
        try:
            metrics_data = message.get("metrics")
            # 存储监控数据
            await self.monitor_service.store_metrics(metrics_data)
            # 检查告警条件
            await self.monitor_service.check_alerts(metrics_data)
        except Exception as e:
            logger.error(f"Error handling metrics: {e}")

    async def _handle_heartbeat(self, slave_id: str, message: Dict[str, Any]):
        """处理心跳消息"""
        try:
            timestamp = message.get("timestamp")
            await self.slave_service.update_slave_status(
                slave_id, "online", datetime.fromisoformat(timestamp)
            )
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")
