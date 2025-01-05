import asyncio
import json
from typing import Dict, List, Optional
import aiohttp
import aiofiles
from pathlib import Path
from ncod.master.core.config import settings
from ncod.master.core.logger import logger
from ncod.master.models.device import Device


class VirtualHereManager:
    """VirtualHere服务器管理器"""

    def __init__(self):
        self.host = settings.VH_SERVER_HOST
        self.port = settings.VH_SERVER_PORT
        self._running = False
        self._devices = {}

    async def start(self):
        """启动VirtualHere管理器"""
        if self._running:
            return
        self._running = True
        logger.info("Starting VirtualHere manager")
        asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """停止VirtualHere管理器"""
        if not self._running:
            return
        self._running = False
        logger.info("Stopping VirtualHere manager")

    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                devices = await self._get_device_list()
                await self._update_device_status(devices)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            await asyncio.sleep(5)

    async def _get_device_list(self) -> List[Dict]:
        """获取设备列表"""
        async with aiohttp.ClientSession() as session:
            url = f"http://{self.host}:{self.port}/api/devices"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return []

    async def _update_device_status(self, devices: List[Dict]):
        """更新设备状态"""
        current_devices = set()
        for device_info in devices:
            device_id = device_info["id"]
            current_devices.add(device_id)

            if device_id not in self._devices:
                await self._add_new_device(device_info)
            else:
                await self._update_existing_device(device_info)

        # 处理已断开的设备
        disconnected = set(self._devices.keys()) - current_devices
        for device_id in disconnected:
            await self._handle_disconnected_device(device_id)

    async def _add_new_device(self, device_info: Dict):
        """添加新设备"""
        device_id = device_info["id"]
        self._devices[device_id] = device_info
        logger.info(f"New device connected: {device_info.get('name', device_id)}")

    async def _update_existing_device(self, device_info: Dict):
        """更新现有设备状态"""
        device_id = device_info["id"]
        self._devices[device_id] = device_info
        logger.info(f"Device updated: {device_info.get('name', device_id)}")

    async def _handle_disconnected_device(self, device_id: str):
        """处理断开连接的设备"""
        device_info = self._devices.pop(device_id)
        logger.info(f"Device disconnected: {device_info.get('name', device_id)}")

    async def get_device_info(self, device_id: str) -> Optional[Dict]:
        """获取设备信息"""
        return self._devices.get(device_id)

    async def connect_device(self, device_id: str, user_id: str) -> bool:
        """连接设备"""
        device_info = self._devices.get(device_id)
        if not device_info:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self.host}:{self.port}/api/connect"
                data = {"device_id": device_id, "user_id": user_id}
                async with session.post(url, json=data) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error connecting device {device_id}: {e}")
            return False

    async def disconnect_device(self, device_id: str) -> bool:
        """断开设备连接"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self.host}:{self.port}/api/disconnect"
                data = {"device_id": device_id}
                async with session.post(url, json=data) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error disconnecting device {device_id}: {e}")
            return False
