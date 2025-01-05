import asyncio
import logging
import re
import subprocess
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class DeviceDiscovery:
    def __init__(self, vh_client_path: str):
        self.vh_client_path = vh_client_path

    async def discover_devices(self) -> List[Dict]:
        """发现本地USB设备"""
        try:
            # 使用VirtualHere客户端列出所有设备
            result = subprocess.run(
                [self.vh_client_path, "list"], capture_output=True, text=True
            )

            if result.returncode != 0:
                logger.error(f"Failed to list devices: {result.stderr}")
                return []

            return self._parse_device_list(result.stdout)

        except Exception as e:
            logger.error(f"Error discovering devices: {e}")
            return []

    def _parse_device_list(self, output: str) -> List[Dict]:
        """解析VirtualHere设备列表输出"""
        devices = []
        current_hub = None

        # 示例输出格式：
        # USB Hub (VID=0000 PID=0000)
        #   |_ Device 1-1: USB Mass Storage Device
        #   |_ Device 1-2: USB Keyboard

        for line in output.split("\n"):
            if not line.strip():
                continue

            if "USB Hub" in line:
                hub_match = re.search(r"VID=(\w+)\s+PID=(\w+)", line)
                if hub_match:
                    current_hub = {"vid": hub_match.group(1), "pid": hub_match.group(2)}
            elif "|_" in line and current_hub:
                device_match = re.search(r"Device\s+(\d+-\d+):\s+(.+)", line)
                if device_match:
                    bus_port = device_match.group(1)
                    name = device_match.group(2)

                    devices.append(
                        {
                            "bus_id": bus_port.split("-")[0],
                            "port": bus_port.split("-")[1],
                            "name": name,
                            "hub_vid": current_hub["vid"],
                            "hub_pid": current_hub["pid"],
                            "discovery_time": datetime.utcnow(),
                        }
                    )

        return devices


class DeviceMonitor:
    def __init__(self, discovery: DeviceDiscovery, device_manager, interval: int = 10):
        self.discovery = discovery
        self.device_manager = device_manager
        self.interval = interval
        self.running = False

    async def start_monitoring(self):
        """开始设备监控"""
        self.running = True

        while self.running:
            try:
                devices = await self.discovery.discover_devices()
                self._update_device_list(devices)
                await asyncio.sleep(self.interval)

            except Exception as e:
                logger.error(f"Error in device monitoring: {e}")
                await asyncio.sleep(self.interval)

    def _update_device_list(self, discovered_devices: List[Dict]):
        """更新设备列表"""
        current_devices = set(self.device_manager.devices.keys())
        discovered_ids = set()

        for device in discovered_devices:
            device_id = f"{device['bus_id']}-{device['port']}"
            discovered_ids.add(device_id)

            if device_id not in current_devices:
                # 新设备
                self.device_manager.register_device(
                    device_id=device_id,
                    bus_id=device["bus_id"],
                    port=device["port"],
                    name=device["name"],
                )
            else:
                # 更新现有设备状态
                self.device_manager.update_device_status(device_id, "online")

        # 标记离线设备
        for device_id in current_devices - discovered_ids:
            self.device_manager.update_device_status(device_id, "offline")

    def stop(self):
        """停止监控"""
        self.running = False
