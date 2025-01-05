"""WebSocket服务器"""

import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from ncod.core.logger import setup_logger
from ncod.master.sync.handler import SyncHandler

logger = setup_logger("websocket_server")


class WebSocketServer:
    """WebSocket服务器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.sync_handler = SyncHandler()

    async def connect(self, websocket: WebSocket, client_id: str):
        """处理连接"""
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            logger.info(f"Client {client_id} connected")
        except Exception as e:
            logger.error(f"Error accepting connection from {client_id}: {e}")
            return

    async def disconnect(self, client_id: str):
        """处理断开连接"""
        try:
            if client_id in self.active_connections:
                await self.active_connections[client_id].close()
                del self.active_connections[client_id]
                logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting client {client_id}: {e}")

    async def handle_message(self, client_id: str, message: str):
        """处理消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "metrics":
                await self.sync_handler.handle_metrics(client_id, data.get("data", {}))
            elif message_type == "device_status":
                await self.sync_handler.handle_device_status(
                    client_id, data.get("data", {})
                )
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client {client_id}")
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")

    async def broadcast(self, message: str):
        """广播消息"""
        disconnected = set()
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.add(client_id)

        # 清理断开的连接
        for client_id in disconnected:
            await self.disconnect(client_id)
