"""从服务器发现服务器"""

import asyncio
import json
from typing import Dict, Set
from datetime import datetime
from ncod.core.heartbeat import HeartbeatMonitor
from ncod.core.logger import setup_logger

logger = setup_logger("discovery_server")


class DiscoveryServer:
    """从服务器发现服务器"""

    def __init__(self):
        self.nodes: Dict[str, Dict] = {}
        self.heartbeat = HeartbeatMonitor()
        self.running = False

    async def start(self):
        """启动服务器"""
        try:
            self.running = True
            await self.heartbeat.start()
            logger.info("Discovery server started")
        except Exception as e:
            logger.error(f"Error starting discovery server: {e}")
            raise

    async def stop(self):
        """停止服务器"""
        try:
            self.running = False
            await self.heartbeat.stop()
            logger.info("Discovery server stopped")
        except Exception as e:
            logger.error(f"Error stopping discovery server: {e}")
            raise

    async def register_node(self, node_id: str, info: Dict) -> bool:
        """注册节点"""
        try:
            self.nodes[node_id] = {"info": info, "registered_at": datetime.utcnow()}
            logger.info(f"Node {node_id} registered")
            return True
        except Exception as e:
            logger.error(f"Error registering node {node_id}: {e}")
            return False

    async def unregister_node(self, node_id: str) -> bool:
        """注销节点"""
        try:
            if node_id in self.nodes:
                del self.nodes[node_id]
                logger.info(f"Node {node_id} unregistered")
            return True
        except Exception as e:
            logger.error(f"Error unregistering node {node_id}: {e}")
            return False

    async def update_node_status(self, node_id: str, status: Dict) -> bool:
        """更新节点状态"""
        try:
            if node_id in self.nodes:
                self.nodes[node_id].update(
                    {"status": status, "last_updated": datetime.utcnow()}
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating node {node_id} status: {e}")
            return False

    def get_active_nodes(self) -> Dict[str, Dict]:
        """获取活跃节点"""
        return {
            node_id: info
            for node_id, info in self.nodes.items()
            if self.heartbeat.is_node_alive(node_id)
        }

    async def handle_heartbeat(self, node_id: str, timestamp: datetime) -> None:
        """处理心跳"""
        try:
            await self.heartbeat.record_heartbeat(node_id, timestamp)
            if node_id in self.nodes:
                self.nodes[node_id]["last_heartbeat"] = timestamp
        except Exception as e:
            logger.error(f"Error handling heartbeat from {node_id}: {e}")
