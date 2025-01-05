from fastapi import WebSocket
from typing import Dict, List
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.slave_connections: Dict[int, WebSocket] = {}
        self.user_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # 移除从服务器连接
        for slave_id, ws in list(self.slave_connections.items()):
            if ws == websocket:
                del self.slave_connections[slave_id]

    async def register_slave(self, slave_id: int, websocket: WebSocket):
        """注册从服务器WebSocket连接"""
        self.slave_connections[slave_id] = websocket

    async def notify_slave(self, slave_id: int, message: dict):
        """向特定从服务器发送消息"""
        if slave_id in self.slave_connections:
            websocket = self.slave_connections[slave_id]
            await websocket.send_json(message)
        else:
            raise Exception("Slave not connected")

    async def broadcast(self, message: dict):
        """广播消息给所有连接的客户端"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting message: {e}")

    async def connect_user(self, websocket: WebSocket, user_id: int):
        """用户WebSocket连接"""
        await websocket.accept()
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)

    async def disconnect_user(self, websocket: WebSocket, user_id: int):
        """断开用户WebSocket连接"""
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def send_stats_update(self, user_id: int, stats_data: dict):
        """发送统计数据更新"""
        if user_id in self.user_connections:
            message = {"type": "stats_update", "data": stats_data}
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending stats update: {e}")
