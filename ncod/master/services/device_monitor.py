"""设备监控服务"""

import asyncio
from typing import Dict, Optional
from datetime import datetime
from ncod.utils.logger import logger
from ncod.master.models.device import Device, DeviceStatus


class DeviceMonitor:
    """设备监控器"""

    def __init__(self):
        self.connected_devices: Dict[str, str] = {}  # device_id -> user_id
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}

    async def connect_device(self, device_id: str, user_id: str) -> bool:
        """连接设备

        Args:
            device_id: 设备ID
            user_id: 用户ID

        Returns:
            bool: 是否连接成功
        """
        if device_id in self.connected_devices:
            return False

        self.connected_devices[device_id] = user_id
        self.monitoring_tasks[device_id] = asyncio.create_task(
            self._monitor_device(device_id)
        )
        logger.info(f"设备已连接: {device_id}, 用户: {user_id}")
        return True

    async def disconnect_device(self, device_id: str) -> bool:
        """断开设备连接

        Args:
            device_id: 设备ID

        Returns:
            bool: 是否断开成功
        """
        if device_id not in self.connected_devices:
            return False

        if device_id in self.monitoring_tasks:
            self.monitoring_tasks[device_id].cancel()
            del self.monitoring_tasks[device_id]

        del self.connected_devices[device_id]
        logger.info(f"设备已断开: {device_id}")
        return True

    async def _monitor_device(self, device_id: str):
        """监控设备状态

        Args:
            device_id: 设备ID
        """
        try:
            while True:
                # 更新设备状态
                await self._update_device_status(device_id)
                # 每5秒检查一次
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info(f"停止监控设备: {device_id}")
        except Exception as e:
            logger.error(f"监控设备出错: {device_id}, 错误: {e}")

    async def _update_device_status(self, device_id: str):
        """更新设备状态

        Args:
            device_id: 设备ID
        """
        try:
            # 这里可以添加实际的设备状态检查逻辑
            # 例如检查设备是否响应、是否有错误等
            pass
        except Exception as e:
            logger.error(f"更新设备状态出错: {device_id}, 错误: {e}")

    def get_device_user(self, device_id: str) -> Optional[str]:
        """获取设备当前使用者

        Args:
            device_id: 设备ID

        Returns:
            Optional[str]: 用户ID，如果设备未连接则返回None
        """
        return self.connected_devices.get(device_id)

    def is_device_connected(self, device_id: str) -> bool:
        """检查设备是否已连接

        Args:
            device_id: 设备ID

        Returns:
            bool: 是否已连接
        """
        return device_id in self.connected_devices


# 创建全局设备监控器实例
device_monitor = DeviceMonitor()
