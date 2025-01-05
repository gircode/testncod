"""故障转移处理器"""

import asyncio
import logging
from typing import Dict, Optional, Set
from datetime import datetime
from ncod.master.discovery.server import DiscoveryServer
from ncod.master.balancer.load_balancer import LoadBalancer

logger = logging.getLogger("failover_handler")


class FailoverHandler:
    """故障转移处理器"""

    def __init__(self, discovery_server: DiscoveryServer, load_balancer: LoadBalancer):
        self.discovery = discovery_server
        self.load_balancer = load_balancer
        self.node_devices: Dict[str, Set[str]] = {}
        self.running = False

    async def start(self):
        """启动处理器"""
        try:
            self.running = True
            logger.info("Failover handler started")
            asyncio.create_task(self._monitor_nodes())
        except Exception as e:
            logger.error(f"Error starting failover handler: {e}")
            self.running = False
            raise

    async def stop(self):
        """停止处理器"""
        try:
            self.running = False
            logger.info("Failover handler stopped")
        except Exception as e:
            logger.error(f"Error stopping failover handler: {e}")
            raise

    def register_device(self, node_id: str, device_id: str):
        """注册设备"""
        try:
            if node_id not in self.node_devices:
                self.node_devices[node_id] = set()
            self.node_devices[node_id].add(device_id)
        except Exception as e:
            logger.error(f"Error registering device: {e}")

    def unregister_device(self, node_id: str, device_id: str):
        """注销设备"""
        try:
            if node_id in self.node_devices:
                self.node_devices[node_id].discard(device_id)
        except Exception as e:
            logger.error(f"Error unregistering device: {e}")

    async def handle_node_failure(self, node_id: str):
        """处理节点故障"""
        try:
            if node_id not in self.node_devices:
                return

            devices = self.node_devices[node_id]
            if not devices:
                return

            # 获取最佳备用节点
            backup_node = self.load_balancer.get_best_node()
            if not backup_node or backup_node == node_id:
                logger.error("No available backup node")
                return

            # 迁移设备到备用节点
            for device_id in devices:
                await self._migrate_device(device_id, node_id, backup_node)

            # 清理原节点设备记录
            self.node_devices[node_id].clear()

        except Exception as e:
            logger.error(f"Error handling node failure: {e}")

    async def _monitor_nodes(self):
        """监控节点状态"""
        while self.running:
            try:
                active_nodes = self.discovery.get_active_nodes()
                current_nodes = set(self.node_devices.keys())

                # 检查节点故障
                for node_id in current_nodes:
                    if node_id not in active_nodes:
                        logger.warning(f"Node {node_id} failed")
                        await self.handle_node_failure(node_id)

            except Exception as e:
                logger.error(f"Error monitoring nodes: {e}")

            await asyncio.sleep(5)

    async def _migrate_device(self, device_id: str, from_node: str, to_node: str):
        """迁移设备"""
        try:
            logger.info(
                f"Migrating device {device_id} " f"from {from_node} to {to_node}"
            )
            # 这里添加实际的设备迁移逻辑
            self.unregister_device(from_node, device_id)
            self.register_device(to_node, device_id)
            logger.info(f"Device {device_id} migrated successfully")
        except Exception as e:
            logger.error(f"Error migrating device: {e}")
