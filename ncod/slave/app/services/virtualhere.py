"""
VirtualHere USB Server集成服务
"""

import asyncio
import logging
import platform
import re
import socket
import subprocess
import telnetlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..core.config import settings
from ..exceptions import VirtualHereError
from ..models.device import DeviceConnection, UsbDevice

logger = logging.getLogger(__name__)


class HardwareInfo:
    """硬件信息收集"""

    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """获取系统信息"""
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
        }

        # Linux系统特定信息
        if info["platform"].lower() == "linux":
            try:
                # 获取CPU序列号
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("Serial"):
                            info["cpu_serial"] = line.split(":")[1].strip()
                            break

                # 获取主板序列号
                result = subprocess.run(
                    ["sudo", "dmidecode", "-s", "system-serial-number"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    info["board_serial"] = result.stdout.strip()
            except Exception as e:
                logger.error(f"获取Linux硬件信息失败: {str(e)}")

        # Windows系统特定信息
        elif info["platform"].lower() == "windows":
            try:
                # 获取CPU ID
                result = subprocess.run(
                    ["wmic", "cpu", "get", "processorid"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    info["cpu_serial"] = result.stdout.split("\n")[1].strip()

                # 获取主板序列号
                result = subprocess.run(
                    ["wmic", "baseboard", "get", "serialnumber"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    info["board_serial"] = result.stdout.split("\n")[1].strip()
            except Exception as e:
                logger.error(f"获取Windows硬件信息失败: {str(e)}")

        return info


class VirtualHereClient:
    """VirtualHere客户端"""

    def __init__(self, host: str = "localhost", port: int = 7575):
        self.host = host
        self.port = port
        self._lock = asyncio.Lock()
        self._connection_cache: Dict[str, Dict] = {}

    async def connect(self) -> telnetlib.Telnet:
        """连接到VirtualHere服务器"""
        try:
            tn = telnetlib.Telnet(self.host, self.port, timeout=5)
            return tn
        except Exception as e:
            raise VirtualHereError(f"连接VirtualHere服务器失败: {str(e)}")

    async def force_detach_device(
        self, device_id: int, admin_id: str, reason: str = "Administrative action"
    ) -> bool:
        """管理员强制断开设备"""
        async with self._lock:
            try:
                tn = await self.connect()

                # 先获取设备当前状态
                device_info = await self.get_device_info(device_id)
                if not device_info:
                    return False

                # 如果设备正在使用中，记录强制断开事件
                if device_info.get("status") == "In Use":
                    connection_key = f"{device_id}:{device_info.get('client_id', '')}"
                    if connection_key in self._connection_cache:
                        conn_info = self._connection_cache[connection_key]
                        await self._log_force_detach(
                            device_id=device_id,
                            user_id=conn_info.get("user_id"),
                            admin_id=admin_id,
                            reason=reason,
                        )

                # 发送强制断开命令
                tn.write(f"force_detach {device_id}\n".encode())
                response = tn.read_until(b"END", timeout=5).decode()

                success = "SUCCESS" in response
                if success:
                    # 清除连接缓存
                    self._connection_cache.pop(connection_key, None)

                return success

            except Exception as e:
                logger.error(f"强制断开设备失败: {str(e)}")
                return False
            finally:
                if "tn" in locals():
                    tn.close()

    async def _log_force_detach(
        self, device_id: int, user_id: str, admin_id: str, reason: str
    ):
        """记录强制断开事件"""
        try:
            event = DeviceConnection(
                device_id=device_id,
                user_id=user_id,
                admin_id=admin_id,
                action="force_detach",
                reason=reason,
                timestamp=datetime.utcnow(),
            )
            self.db.add(event)
            await self.db.commit()
        except Exception as e:
            logger.error(f"记录强制断开事件失败: {str(e)}")
            await self.db.rollback()

    async def attach_device(
        self,
        device_id: int,
        client_id: str,
        user_id: str,
        hardware_info: Dict[str, str],
    ) -> bool:
        """将设备分配给客户端，包含硬件验证"""
        async with self._lock:
            try:
                # 验证硬件信息
                if not self._verify_hardware_info(hardware_info):
                    logger.warning(f"硬件信息验证失败: {client_id}")
                    return False

                tn = await self.connect()

                # 发送attach命令
                tn.write(f"attach {device_id} {client_id}\n".encode())
                response = tn.read_until(b"END", timeout=5).decode()

                success = "SUCCESS" in response
                if success:
                    # 缓存连接信息
                    self._connection_cache[f"{device_id}:{client_id}"] = {
                        "user_id": user_id,
                        "hardware_info": hardware_info,
                        "connected_at": datetime.utcnow(),
                    }

                return success

            except Exception as e:
                logger.error(f"分配设备失败: {str(e)}")
                return False
            finally:
                if "tn" in locals():
                    tn.close()

    def _verify_hardware_info(self, hardware_info: Dict[str, str]) -> bool:
        """验证硬件信息"""
        required_fields = ["platform", "cpu_serial", "board_serial"]
        return all(field in hardware_info for field in required_fields)

    async def list_devices(self) -> List[Dict]:
        """获取设备列表"""
        async with self._lock:
            try:
                tn = await self.connect()

                # 发送list命令
                tn.write(b"list\n")
                response = tn.read_until(b"END", timeout=5).decode()

                devices = []
                current_hub = None

                for line in response.split("\n"):
                    line = line.strip()

                    # 解析Hub信息
                    hub_match = re.match(r"Hub #(\d+) \((.*?)\)", line)
                    if hub_match:
                        current_hub = {
                            "id": int(hub_match.group(1)),
                            "name": hub_match.group(2),
                        }
                        continue

                    # 解析设备信息
                    device_match = re.match(r"Device #(\d+) \((.*?)\) \[(.*?)\]", line)
                    if device_match and current_hub:
                        device = {
                            "id": int(device_match.group(1)),
                            "name": device_match.group(2),
                            "status": device_match.group(3),
                            "hub_id": current_hub["id"],
                            "hub_name": current_hub["name"],
                        }
                        devices.append(device)

                return devices

            except Exception as e:
                raise VirtualHereError(f"获取设备列表失败: {str(e)}")
            finally:
                if "tn" in locals():
                    tn.close()

    async def get_device_info(self, device_id: int) -> Optional[Dict]:
        """获取设备详细信息"""
        async with self._lock:
            try:
                tn = await self.connect()

                # 发送info命令
                tn.write(f"info {device_id}\n".encode())
                response = tn.read_until(b"END", timeout=5).decode()

                info = {}
                for line in response.split("\n"):
                    line = line.strip()
                    if ":" in line:
                        key, value = line.split(":", 1)
                        info[key.strip()] = value.strip()

                return info if info else None

            except Exception as e:
                raise VirtualHereError(f"获取设备信息失败: {str(e)}")
            finally:
                if "tn" in locals():
                    tn.close()

    async def detach_device(self, device_id: int) -> bool:
        """释放设备"""
        async with self._lock:
            try:
                tn = await self.connect()

                # 发送detach命令
                tn.write(f"detach {device_id}\n".encode())
                response = tn.read_until(b"END", timeout=5).decode()

                return "SUCCESS" in response

            except Exception as e:
                raise VirtualHereError(f"释放设备失败: {str(e)}")
            finally:
                if "tn" in locals():
                    tn.close()

    async def get_client_list(self) -> List[Dict]:
        """获取客户端列表"""
        async with self._lock:
            try:
                tn = await self.connect()

                # 发送clients命令
                tn.write(b"clients\n")
                response = tn.read_until(b"END", timeout=5).decode()

                clients = []
                for line in response.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("Clients"):
                        client_match = re.match(r"(\d+)\. (.*?) \((.*?)\)", line)
                        if client_match:
                            client = {
                                "id": int(client_match.group(1)),
                                "name": client_match.group(2),
                                "ip": client_match.group(3),
                            }
                            clients.append(client)

                return clients

            except Exception as e:
                raise VirtualHereError(f"获取客户端列表失败: {str(e)}")
            finally:
                if "tn" in locals():
                    tn.close()


class VirtualHereService:
    """VirtualHere服务"""

    def __init__(self):
        self.client = VirtualHereClient(
            settings.VIRTUALHERE_HOST, settings.VIRTUALHERE_PORT
        )
        self._device_cache = {}
        self._last_update = datetime.min

    async def sync_devices(self) -> List[UsbDevice]:
        """同步设备状态"""
        try:
            # 获取设备列表
            devices = await self.client.list_devices()

            # 更新设备缓存
            current_time = datetime.utcnow()
            for device in devices:
                device_id = f"{device['hub_id']}:{device['id']}"
                if device_id in self._device_cache:
                    # 更新现有设备状态
                    self._device_cache[device_id].update(
                        {"status": device["status"], "last_seen": current_time}
                    )
                else:
                    # 添加新设备
                    self._device_cache[device_id] = {
                        "hub_id": device["hub_id"],
                        "device_id": device["id"],
                        "name": device["name"],
                        "status": device["status"],
                        "first_seen": current_time,
                        "last_seen": current_time,
                    }

            # 清理离线设备
            offline_threshold = current_time - settings.DEVICE_OFFLINE_THRESHOLD
            offline_devices = [
                device_id
                for device_id, device in self._device_cache.items()
                if device["last_seen"] < offline_threshold
            ]
            for device_id in offline_devices:
                del self._device_cache[device_id]

            self._last_update = current_time
            return list(self._device_cache.values())

        except Exception as e:
            logger.error(f"同步设备状态失败: {str(e)}")
            return []

    async def get_device_status(self, hub_id: int, device_id: int) -> Optional[Dict]:
        """获取设备状态"""
        device_key = f"{hub_id}:{device_id}"
        return self._device_cache.get(device_key)

    async def attach_device_to_client(
        self, hub_id: int, device_id: int, client_id: str
    ) -> bool:
        """将设备分配给客户端"""
        try:
            # 检查设备状态
            status = await self.get_device_status(hub_id, device_id)
            if not status or status["status"] != "Available":
                return False

            # 分配设备
            success = await self.client.attach_device(device_id, client_id)
            if success:
                # 更新缓存
                device_key = f"{hub_id}:{device_id}"
                if device_key in self._device_cache:
                    self._device_cache[device_key]["status"] = "In Use"

            return success

        except Exception as e:
            logger.error(f"分配设备失败: {str(e)}")
            return False

    async def detach_device(self, hub_id: int, device_id: int) -> bool:
        """释放设备"""
        try:
            success = await self.client.detach_device(device_id)
            if success:
                # 更新缓存
                device_key = f"{hub_id}:{device_id}"
                if device_key in self._device_cache:
                    self._device_cache[device_key]["status"] = "Available"

            return success

        except Exception as e:
            logger.error(f"释放设备失败: {str(e)}")
            return False
