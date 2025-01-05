"""设备控制器"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.slave.device.virtualhere import VirtualHereClient

logger = setup_logger("device_controller")


class DeviceController:
    """设备控制器"""

    def __init__(self):
        self.vh_client = VirtualHereClient(
            host=config.virtualhere_host,
            port=config.virtualhere_port,
            api_key=config.virtualhere_api_key,
        )
        self.devices: Dict[str, Dict] = {}
        self.running = False

    async def start(self):
        """启动控制器"""
        try:
            self.running = True
            await self.vh_client.connect()
            asyncio.create_task(self._device_scan_loop())
            logger.info("Device controller started")
        except Exception as e:
            logger.error(f"Error starting device controller: {e}")
            raise

    async def stop(self):
        """停止控制器"""
        try:
            self.running = False
            await self.vh_client.disconnect()
            logger.info("Device controller stopped")
        except Exception as e:
            logger.error(f"Error stopping device controller: {e}")
            raise

    async def _device_scan_loop(self):
        """设备扫描循环"""
        while self.running:
            try:
                await self.scan_devices()
                await asyncio.sleep(config.device_scan_interval)
            except Exception as e:
                logger.error(f"Error in device scan loop: {e}")
                await asyncio.sleep(5)

    async def scan_devices(self):
        """扫描设备"""
        try:
            devices = await self.vh_client.list_devices()
            current_devices = set(self.devices.keys())
            scanned_devices = set()

            for device in devices:
                device_id = device["serial_number"]
                scanned_devices.add(device_id)

                if device_id not in self.devices:
                    # 新设备
                    self.devices[device_id] = {
                        "info": device,
                        "status": "available",
                        "last_seen": datetime.utcnow(),
                    }
                    logger.info(f"New device detected: {device_id}")
                else:
                    # 更新设备状态
                    self.devices[device_id].update(
                        {"info": device, "last_seen": datetime.utcnow()}
                    )

            # 处理已断开的设备
            for device_id in current_devices - scanned_devices:
                if self.devices[device_id]["status"] != "disconnected":
                    self.devices[device_id]["status"] = "disconnected"
                    logger.info(f"Device disconnected: {device_id}")

        except Exception as e:
            logger.error(f"Error scanning devices: {e}")

    async def connect_device(self, device_id: str, user_id: str) -> bool:
        """连接设备"""
        try:
            device = self.devices.get(device_id)
            if not device:
                logger.error(f"Device {device_id} not found")
                return False

            if device["status"] != "available":
                logger.error(f"Device {device_id} not available")
                return False

            success = await self.vh_client.connect_device(device_id, user_id)
            if success:
                device["status"] = "in_use"
                device["user_id"] = user_id
                device["connected_at"] = datetime.utcnow()
                logger.info(f"Device {device_id} connected by user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Error connecting device {device_id}: {e}")
            return False

    async def disconnect_device(self, device_id: str) -> bool:
        """断开设备"""
        try:
            device = self.devices.get(device_id)
            if not device:
                logger.error(f"Device {device_id} not found")
                return False

            success = await self.vh_client.disconnect_device(device_id)
            if success:
                device["status"] = "available"
                device.pop("user_id", None)
                device.pop("connected_at", None)
                logger.info(f"Device {device_id} disconnected")
            return success
        except Exception as e:
            logger.error(f"Error disconnecting device {device_id}: {e}")
            return False

    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """获取设备信息"""
        try:
            device = self.devices.get(device_id)
            if device:
                return {
                    "id": device_id,
                    "status": device["status"],
                    "vendor_id": device["info"]["vendor_id"],
                    "product_id": device["info"]["product_id"],
                    "type": device["info"].get("type", "unknown"),
                }
            return None
        except Exception as e:
            logger.error(f"Error getting device info for {device_id}: {e}")
            return None

    def get_all_devices(self) -> List[Dict]:
        """获取所有设备信息"""
        return [
            self.get_device_info(device_id)
            for device_id in self.devices
            if self.get_device_info(device_id)
        ]


# 创建全局设备控制器实例
device_controller = DeviceController()
