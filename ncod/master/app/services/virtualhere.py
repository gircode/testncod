"""
VirtualHere服务
"""

import asyncio
import logging
from typing import Dict, List, Optional

import aiohttp
from fastapi import HTTPException, status

from ..core.config import settings

# 配置日志
logger = logging.getLogger(__name__)


class VirtualHereService:
    def __init__(self):
        self.base_url = f"http://{settings.VIRTUALHERE_SERVER_HOST}:{settings.VIRTUALHERE_SERVER_PORT}"
        self.api_key = settings.VIRTUALHERE_API_KEY

    async def _make_request(
        self, endpoint: str, method: str = "GET", data: Optional[Dict] = None
    ) -> Dict:
        """发送请求到VirtualHere服务器"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                }

                url = f"{self.base_url}/api/{endpoint}"

                async with session.request(
                    method, url, headers=headers, json=data
                ) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"VirtualHere服务器返回错误: {await response.text()}",
                        )

                    return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"VirtualHere请求失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="VirtualHere服务不可用",
            )

    async def list_devices(self) -> List[Dict]:
        """获取所有USB设备列表"""
        try:
            response = await self._make_request("devices")
            return response.get("devices", [])

        except Exception as e:
            logger.error(f"获取设备列表失败: {str(e)}")
            raise

    async def get_device_info(self, device_id: str) -> Dict:
        """获取设备详细信息"""
        try:
            response = await self._make_request(f"devices/{device_id}")
            return response

        except Exception as e:
            logger.error(f"获取设备信息失败: {str(e)}")
            raise

    async def connect_device(
        self, device_id: str, user_id: str, client_ip: str
    ) -> bool:
        """连接设备到用户"""
        try:
            data = {"user_id": user_id, "client_ip": client_ip}

            await self._make_request(
                f"devices/{device_id}/connect", method="POST", data=data
            )
            return True

        except Exception as e:
            logger.error(f"连接设备失败: {str(e)}")
            raise

    async def disconnect_device(self, device_id: str) -> bool:
        """断开设备连接"""
        try:
            await self._make_request(f"devices/{device_id}/disconnect", method="POST")
            return True

        except Exception as e:
            logger.error(f"断开设备失败: {str(e)}")
            raise

    async def get_device_status(self, device_id: str) -> Dict:
        """获取设备状态"""
        try:
            response = await self._make_request(f"devices/{device_id}/status")
            return response

        except Exception as e:
            logger.error(f"获取设备状态失败: {str(e)}")
            raise

    async def check_device_availability(self, device_id: str) -> bool:
        """检查设备是否可用"""
        try:
            status = await self.get_device_status(device_id)
            return status.get("available", False)

        except Exception as e:
            logger.error(f"检查设备可用性失败: {str(e)}")
            raise

    async def get_connected_devices(self, user_id: str) -> List[Dict]:
        """获取用户已连接的设备"""
        try:
            response = await self._make_request(f"users/{user_id}/devices")
            return response.get("devices", [])

        except Exception as e:
            logger.error(f"获取用户已连接设备失败: {str(e)}")
            raise

    async def monitor_device_status(self, device_id: str, callback):
        """监控设备状态变化"""
        while True:
            try:
                status = await self.get_device_status(device_id)
                await callback(status)

            except Exception as e:
                logger.error(f"监控设备状态失败: {str(e)}")

            await asyncio.sleep(settings.DEVICE_HEARTBEAT_INTERVAL)

    async def get_server_info(self) -> Dict:
        """获取服务器信息"""
        try:
            response = await self._make_request("server/info")
            return response

        except Exception as e:
            logger.error(f"获取服务器信息失败: {str(e)}")
            raise
