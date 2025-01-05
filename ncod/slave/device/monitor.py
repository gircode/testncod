"""设备状态监控器"""

import asyncio
from typing import Dict, Optional
from datetime import datetime
from ncod.core.logger import setup_logger

logger = setup_logger("device_monitor")


class DeviceMonitor:
    """设备状态监控器"""

    def __init__(self, device_manager):
        self.device_manager = device_manager
        self.device_status: Dict[str, Dict] = {}
        self.running = False

    async def start(self):
        """启动监控器"""
        try:
            self.running = True
            logger.info("Device monitor starting...")
            asyncio.create_task(self._monitor_devices())
            logger.info("Device monitor started")
        except Exception as e:
            logger.error(f"Error starting device monitor: {e}")
            self.running = False
            raise

    async def stop(self):
        """停止监控器"""
        try:
            self.running = False
            logger.info("Device monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping device monitor: {e}")
            raise

    async def _monitor_devices(self):
        """监控设备状态"""
        while self.running:
            try:
                devices = self.device_manager.get_all_devices()
                for device_id, device in devices.items():
                    status = await self._check_device_status(device)
                    self.device_status[device_id] = {
                        "status": status,
                        "last_check": datetime.utcnow(),
                    }
            except Exception as e:
                logger.error(f"Error monitoring devices: {e}")
            await asyncio.sleep(5)

    async def _check_device_status(self, device: Dict) -> str:
        """检查设备状态"""
        try:
            # 这里添加实际的设备状态检查逻辑
            # 示例返回 "online"
            return "online"
        except Exception as e:
            logger.error(f"Error checking device status: {e}")
            return "unknown"

    def get_device_status(self, device_id: str) -> Optional[Dict]:
        """获取设备状态"""
        return self.device_status.get(device_id)

    def get_all_status(self) -> Dict[str, Dict]:
        """获取所有设备状态"""
        return self.device_status.copy()
