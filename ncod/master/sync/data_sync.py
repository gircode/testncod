"""数据同步处理器"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime
from ncod.master.discovery.server import DiscoveryServer

logger = logging.getLogger("data_sync")


class DataSyncHandler:
    """数据同步处理器"""

    def __init__(self, discovery_server: DiscoveryServer):
        self.discovery = discovery_server
        self.sync_data: Dict[str, Dict] = {}
        self.sync_timestamps: Dict[str, datetime] = {}
        self.running = False

    async def start(self):
        """启动同步处理器"""
        try:
            self.running = True
            logger.info("Data sync handler started")
            asyncio.create_task(self._sync_loop())
        except Exception as e:
            logger.error(f"Error starting data sync handler: {e}")
            self.running = False
            raise

    async def stop(self):
        """停止同步处理器"""
        try:
            self.running = False
            logger.info("Data sync handler stopped")
        except Exception as e:
            logger.error(f"Error stopping data sync handler: {e}")
            raise

    async def update_data(self, node_id: str, data: Dict):
        """更新节点数据"""
        try:
            self.sync_data[node_id] = data
            self.sync_timestamps[node_id] = datetime.utcnow()
            await self._notify_nodes(node_id, data)
        except Exception as e:
            logger.error(f"Error updating data for node {node_id}: {e}")

    async def get_node_data(self, node_id: str) -> Optional[Dict]:
        """获取节点数据"""
        return self.sync_data.get(node_id)

    async def _sync_loop(self):
        """同步循环"""
        while self.running:
            try:
                active_nodes = self.discovery.get_active_nodes()
                for node_id in active_nodes:
                    if node_id not in self.sync_timestamps:
                        continue

                    # 检查数据是否需要同步
                    last_sync = self.sync_timestamps[node_id]
                    if (datetime.utcnow() - last_sync).total_seconds() > 300:
                        await self._sync_node_data(node_id)

            except Exception as e:
                logger.error(f"Error in sync loop: {e}")

            await asyncio.sleep(60)

    async def _sync_node_data(self, node_id: str):
        """同步节点数据"""
        try:
            data = self.sync_data.get(node_id)
            if data:
                await self._notify_nodes(node_id, data)
                self.sync_timestamps[node_id] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error syncing data for node {node_id}: {e}")

    async def _notify_nodes(self, source_node: str, data: Dict):
        """通知其他节点"""
        try:
            active_nodes = self.discovery.get_active_nodes()
            for node_id in active_nodes:
                if node_id != source_node:
                    await self._send_sync_data(node_id, data)
        except Exception as e:
            logger.error(f"Error notifying nodes: {e}")

    async def _send_sync_data(self, node_id: str, data: Dict):
        """发送同步数据"""
        try:
            # 这里添加实际的数据发送逻辑
            logger.debug(f"Sending sync data to node {node_id}")
        except Exception as e:
            logger.error(f"Error sending sync data to node {node_id}: {e}")
