"""
设备管理模块
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

logger = logging.getLogger(__name__)


class DeviceStatus:
    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTED = "connected"
    ERROR = "error"


class DeviceManager:
    def __init__(self, config: dict):
        self.vh_server_path = config["vh_server_path"]
        self.vh_client_path = config["vh_client_path"]
        self.devices: Dict[str, dict] = {}
        self.vh_server_process: Optional[subprocess.Popen] = None
        self.status_callbacks: List[callable] = []
        self.max_connect_retries = config.get("max_connect_retries", 3)
        self.connect_retry_delay = config.get("connect_retry_delay", 2)

    def add_status_callback(self, callback: callable):
        """添加状态变更回调函数"""
        self.status_callbacks.append(callback)

    def _notify_status_change(self, device_id: str, status: str):
        """通知状态变更"""
        for callback in self.status_callbacks:
            try:
                callback(device_id, status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")

    async def start_server(self) -> bool:
        """启动VirtualHere服务器"""
        try:
            self.vh_server_process = subprocess.Popen(
                [self.vh_server_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            logger.info("VirtualHere server started")
            return True
        except Exception as e:
            logger.error(f"Failed to start VirtualHere server: {e}")
            return False

    async def stop_server(self):
        """停止VirtualHere服务器"""
        if self.vh_server_process:
            self.vh_server_process.terminate()
            await asyncio.sleep(1)
            if self.vh_server_process.poll() is None:
                self.vh_server_process.kill()
            logger.info("VirtualHere server stopped")

    def register_device(self, device_id: str, bus_id: str, port: str, name: str):
        """注册设备"""
        self.devices[device_id] = {
            "bus_id": bus_id,
            "port": port,
            "name": name,
            "status": DeviceStatus.ONLINE,
            "connected_user": None,
            "connected_time": None,
            "last_seen": datetime.utcnow(),
            "error_message": None,
        }
        logger.info(f"Device {device_id} ({name}) registered")
        self._notify_status_change(device_id, DeviceStatus.ONLINE)

    def update_device_status(
        self, device_id: str, status: str, error_message: str = None
    ):
        """更新设备状态"""
        if device_id in self.devices:
            device = self.devices[device_id]
            old_status = device["status"]
            device["status"] = status
            device["last_seen"] = datetime.utcnow()
            device["error_message"] = error_message

            if old_status != status:
                logger.info(
                    f"Device {device_id} status changed: {old_status} -> {status}"
                )
                self._notify_status_change(device_id, status)

    def get_device_info(self, device_id: str) -> Optional[dict]:
        """获取设备信息"""
        return self.devices.get(device_id)

    def get_all_devices(self) -> List[dict]:
        """获取所有设备信息"""
        return [
            {"id": device_id, **device_info}
            for device_id, device_info in self.devices.items()
        ]

    async def connect_device(self, device_id: int, user_id: int) -> bool:
        """连接设备，带重试机制"""
        device = self.devices.get(device_id)
        if not device:
            logger.error(f"Device {device_id} not found")
            return False

        for attempt in range(self.max_connect_retries):
            try:
                success = await self._try_connect_device(device)
                if success:
                    device["status"] = "connected"
                    device["connected_user"] = user_id
                    device["connected_time"] = datetime.utcnow()
                    logger.info(f"Device {device_id} connected successfully")
                    return True

                logger.warning(
                    f"Connect attempt {attempt + 1} failed for device {device_id}"
                )

            except Exception as e:
                logger.error(
                    f"Error connecting device {device_id} (attempt {attempt + 1}): {e}"
                )

            if attempt < self.max_connect_retries - 1:
                retry_delay = self.connect_retry_delay * (2**attempt)
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)

        logger.error(
            f"Failed to connect device {device_id} after {self.max_connect_retries} attempts"
        )
        return False

    async def _try_connect_device(self, device: dict) -> bool:
        """尝试连接设备"""
        try:
            result = subprocess.run(
                [self.vh_client_path, "use", f"{device['bus_id']},{device['port']}"],
                capture_output=True,
                text=True,
                timeout=10,  # 设置超时时间
            )

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            logger.error("Device connection timeout")
            return False
        except Exception as e:
            logger.error(f"Error in device connection: {e}")
            return False
