import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple
import aiohttp
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class VirtualHereManager:
    def __init__(self, config: Dict):
        self.config = config
        self.vh_server_path = config.get("vh_server_path", "/usr/bin/vhusbd")
        self.vh_client_path = config.get("vh_client_path", "/usr/bin/vhclient")
        self.device_stats = {}  # 设备使用统计
        self.connected_devices = {}  # 当前连接的设备
        self.reconnect_attempts = {}  # 重连尝试次数
        self.stats_file = config.get("stats_file", "device_stats.json")
        self.max_reconnect_attempts = config.get("max_reconnect_attempts", 3)
        self.reconnect_interval = config.get("reconnect_interval", 5)
        self.load_stats()

    def load_stats(self):
        """加载设备使用统计数据"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, "r") as f:
                    self.device_stats = json.load(f)
        except Exception as e:
            logger.error(f"Error loading device stats: {e}")

    def save_stats(self):
        """保存设备使用统计数据"""
        try:
            with open(self.stats_file, "w") as f:
                json.dump(self.device_stats, f)
        except Exception as e:
            logger.error(f"Error saving device stats: {e}")

    async def start_server(self) -> bool:
        """启动VirtualHere服务器"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.vh_server_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Failed to start VirtualHere server: {stderr.decode()}")
                return False

            logger.info("VirtualHere server started successfully")
            # 启动设备监控
            asyncio.create_task(self.monitor_devices())
            return True

        except Exception as e:
            logger.error(f"Error starting VirtualHere server: {e}")
            return False

    async def get_device_list(self) -> List[Dict]:
        """获取所有USB设备列表"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.vh_client_path,
                "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Failed to get device list: {stderr.decode()}")
                return []

            return self._parse_device_list(stdout.decode())

        except Exception as e:
            logger.error(f"Error getting device list: {e}")
            return []

    async def connect_device(self, device_id: str, user_id: str) -> bool:
        """连接设备并记录使用情况"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.vh_client_path,
                "use",
                device_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self.connected_devices[device_id] = {
                    "user_id": user_id,
                    "connected_at": datetime.now().isoformat(),
                    "last_seen": time.time(),
                }
                self._update_device_stats(device_id, user_id, "connect")
                return True
            else:
                logger.error(f"Failed to connect device {device_id}: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error connecting device {device_id}: {e}")
            return False

    async def disconnect_device(self, device_id: str) -> bool:
        """断开设备连接并更新使用记录"""
        try:
            if device_id in self.connected_devices:
                process = await asyncio.create_subprocess_exec(
                    self.vh_client_path,
                    "stop",
                    device_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    user_id = self.connected_devices[device_id]["user_id"]
                    self._update_device_stats(device_id, user_id, "disconnect")
                    del self.connected_devices[device_id]
                    return True

            return False

        except Exception as e:
            logger.error(f"Error disconnecting device {device_id}: {e}")
            return False

    def _update_device_stats(self, device_id: str, user_id: str, action: str):
        """更新设备使用统计"""
        if device_id not in self.device_stats:
            self.device_stats[device_id] = {
                "total_usage_time": 0,
                "connection_count": 0,
                "last_connected": None,
                "users": {},
            }

        if action == "connect":
            self.device_stats[device_id]["connection_count"] += 1
            self.device_stats[device_id]["last_connected"] = datetime.now().isoformat()

            if user_id not in self.device_stats[device_id]["users"]:
                self.device_stats[device_id]["users"][user_id] = {
                    "total_usage_time": 0,
                    "connection_count": 0,
                }

            self.device_stats[device_id]["users"][user_id]["connection_count"] += 1

        elif action == "disconnect":
            if device_id in self.connected_devices:
                connected_at = datetime.fromisoformat(
                    self.connected_devices[device_id]["connected_at"]
                )
                usage_time = (datetime.now() - connected_at).total_seconds()
                self.device_stats[device_id]["total_usage_time"] += usage_time
                self.device_stats[device_id]["users"][user_id][
                    "total_usage_time"
                ] += usage_time

        self.save_stats()

    async def monitor_devices(self):
        """监控设备状态并处理断开重连"""
        while True:
            try:
                current_devices = await self.get_device_list()
                current_device_ids = {d["id"] for d in current_devices if "id" in d}

                # 检查设备状态
                for device_id in list(self.connected_devices.keys()):
                    if device_id not in current_device_ids:
                        if await self._handle_device_disconnect(device_id):
                            logger.info(f"Device {device_id} reconnected successfully")
                        else:
                            logger.warning(
                                f"Device {device_id} disconnected and failed to reconnect"
                            )

                # 更新设备最后可见时间
                for device_id in current_device_ids:
                    if device_id in self.connected_devices:
                        self.connected_devices[device_id]["last_seen"] = time.time()

            except Exception as e:
                logger.error(f"Error in device monitor: {e}")

            await asyncio.sleep(5)  # 每5秒检查一次

    async def _handle_device_disconnect(self, device_id: str) -> bool:
        """处理设备断开事件"""
        if device_id not in self.reconnect_attempts:
            self.reconnect_attempts[device_id] = 0

        while self.reconnect_attempts[device_id] < self.max_reconnect_attempts:
            logger.info(
                f"Attempting to reconnect device {device_id}, attempt {self.reconnect_attempts[device_id] + 1}"
            )

            if await self.connect_device(
                device_id, self.connected_devices[device_id]["user_id"]
            ):
                self.reconnect_attempts[device_id] = 0
                return True

            self.reconnect_attempts[device_id] += 1
            await asyncio.sleep(self.reconnect_interval)

        # 重连失败，清理设备状态
        if device_id in self.connected_devices:
            await self.disconnect_device(device_id)

        self.reconnect_attempts.pop(device_id, None)
        return False

    def _parse_device_list(self, output: str) -> List[Dict]:
        """解析VirtualHere设备列表输出"""
        devices = []
        current_device = {}

        for line in output.split("\n"):
            if line.startswith("Device "):
                if current_device:
                    devices.append(current_device)
                current_device = {
                    "id": line[7:].strip(),
                    "name": line[7:].strip(),
                    "status": "available",
                }
            elif ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                current_device[key] = value.strip()

        if current_device:
            devices.append(current_device)

        return devices
