"""WebSocket管理模块"""

from typing import Dict, Set, Any
from fastapi import WebSocket
from ncod.utils.logger import logger


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, device_id: int, websocket: WebSocket):
        """建立WebSocket连接"""
        await websocket.accept()
        if device_id not in self.active_connections:
            self.active_connections[device_id] = set()
        self.active_connections[device_id].add(websocket)
        logger.info(f"WebSocket连接建立: device_id={device_id}")

    async def disconnect(self, device_id: int, websocket: WebSocket):
        """断开WebSocket连接"""
        if device_id in self.active_connections:
            self.active_connections[device_id].remove(websocket)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]
        logger.info(f"WebSocket连接断开: device_id={device_id}")

    async def broadcast(self, device_id: int, message: Dict[str, Any]):
        """广播消息到指定设备的所有连接"""
        if device_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[device_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"发送WebSocket消息失败: {str(e)}")
                    disconnected.add(connection)

            # 清理断开的连接
            for connection in disconnected:
                await self.disconnect(device_id, connection)


websocket_manager = WebSocketManager()
