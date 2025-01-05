"""负载均衡器"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from ncod.core.logger import setup_logger
from ncod.master.discovery.server import DiscoveryServer

logger = setup_logger("load_balancer")


class LoadBalancer:
    """负载均衡器"""

    def __init__(self, discovery_server: DiscoveryServer):
        self.discovery = discovery_server
        self.node_loads: Dict[str, float] = {}
        self.device_assignments: Dict[str, str] = {}  # device_id -> node_id

    async def update_node_load(self, node_id: str, metrics: Dict) -> None:
        """更新节点负载"""
        try:
            # 计算综合负载分数 (0-1)
            cpu_load = metrics.get("cpu_usage", 0) / 100
            mem_load = metrics.get("memory_usage", 0) / 100
            device_load = metrics.get("device_count", 0) / metrics.get("max_devices", 1)

            # 加权平均
            self.node_loads[node_id] = (
                cpu_load * 0.3 + mem_load * 0.3 + device_load * 0.4
            )

            logger.debug(f"Updated load for node {node_id}: {self.node_loads[node_id]}")
        except Exception as e:
            logger.error(f"Error updating node load: {e}")

    def get_best_node(self, device_type: Optional[str] = None) -> Optional[str]:
        """获取最佳节点"""
        try:
            active_nodes = self.discovery.get_active_nodes()
            candidates = []

            for node_id, info in active_nodes.items():
                # 检查节点是否支持设备类型
                if device_type:
                    supported_types = (
                        info.get("info", {})
                        .get("capabilities", {})
                        .get("supported_types", [])
                    )
                    if device_type not in supported_types:
                        continue

                # 获取节点负载
                load = self.node_loads.get(node_id, 0)
                candidates.append((node_id, load))

            if not candidates:
                return None

            # 选择负载最低的节点
            return min(candidates, key=lambda x: x[1])[0]
        except Exception as e:
            logger.error(f"Error getting best node: {e}")
            return None

    async def assign_device(
        self, device_id: str, device_type: Optional[str] = None
    ) -> Optional[str]:
        """分配设备到节点"""
        try:
            node_id = self.get_best_node(device_type)
            if node_id:
                self.device_assignments[device_id] = node_id
                logger.info(f"Assigned device {device_id} to node {node_id}")
                return node_id
            return None
        except Exception as e:
            logger.error(f"Error assigning device: {e}")
            return None

    def get_device_node(self, device_id: str) -> Optional[str]:
        """获取设备所在节点"""
        return self.device_assignments.get(device_id)

    def remove_device(self, device_id: str) -> None:
        """移除设备分配"""
        try:
            if device_id in self.device_assignments:
                del self.device_assignments[device_id]
                logger.info(f"Removed device assignment for {device_id}")
        except Exception as e:
            logger.error(f"Error removing device assignment: {e}")

    def get_node_devices(self, node_id: str) -> List[str]:
        """获取节点上的设备"""
        return [
            device_id
            for device_id, assigned_node in self.device_assignments.items()
            if assigned_node == node_id
        ]

    def rebalance_devices(self) -> List[Tuple[str, str, str]]:
        """重新平衡设备分配"""
        try:
            migrations = []
            high_load_threshold = 0.8
            load_diff_threshold = 0.3

            # 检查负载过高的节点
            for node_id, load in self.node_loads.items():
                if load > high_load_threshold:
                    devices = self.get_node_devices(node_id)
                    for device_id in devices:
                        # 尝试找到负载更低的节点
                        new_node = self.get_best_node()
                        if (
                            new_node
                            and self.node_loads.get(new_node, 0)
                            < load - load_diff_threshold
                        ):
                            migrations.append((device_id, node_id, new_node))

            return migrations
        except Exception as e:
            logger.error(f"Error rebalancing devices: {e}")
            return []
