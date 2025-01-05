"""WebSocket通信服务"""

import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from ncod.utils.logger import logger


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "device": set(),  # 设备状态订阅
            "monitoring": set(),  # 监控数据订阅
            "alerts": set(),  # 告警信息订阅
        }

    async def connect(self, websocket: WebSocket, client_type: str):
        """建立WebSocket连接

        Args:
            websocket: WebSocket连接
            client_type: 客户端类型
        """
        await websocket.accept()
        if client_type not in self.active_connections:
            self.active_connections[client_type] = set()
        self.active_connections[client_type].add(websocket)
        logger.info(f"WebSocket客户端连接: {client_type}")

    def disconnect(self, websocket: WebSocket, client_type: str):
        """断开WebSocket连接

        Args:
            websocket: WebSocket连接
            client_type: 客户端类型
        """
        self.active_connections[client_type].remove(websocket)
        logger.info(f"WebSocket客户端断开: {client_type}")

    async def broadcast(self, message: dict, client_type: str):
        """广播消息

        Args:
            message: 消息内容
            client_type: 客户端类型
        """
        if client_type in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[client_type]:
                try:
                    await connection.send_json(message)
                except WebSocketDisconnect:
                    disconnected.add(connection)
                except Exception as e:
                    logger.error(f"发送WebSocket消息失败: {e}")
                    disconnected.add(connection)

            # 清理断开的连接
            for connection in disconnected:
                self.active_connections[client_type].remove(connection)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息

        Args:
            message: 消息内容
            websocket: WebSocket连接
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送个人WebSocket消息失败: {e}")


# 创建全局WebSocket管理器实例
websocket_manager = WebSocketManager()
