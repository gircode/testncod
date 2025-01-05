"""USB设备控制器"""

import os
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass

from ncod.utils.usb_utils import USBDevice, usb_scanner
from ncod.utils.logger import logger


@dataclass
class PortStatus:
    """端口状态"""

    port_number: int
    is_enabled: bool
    current_device: Optional[USBDevice] = None
    is_authorized: bool = False


class USBController:
    """USB设备控制器"""

    def __init__(self):
        self._port_status: Dict[int, PortStatus] = {}
        self._scan_interval: int = 2  # 扫描间隔(秒)
        self._scan_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动控制器"""
        self._scan_task = asyncio.create_task(self._scan_loop())

    async def stop(self):
        """停止控制器"""
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass

    async def _scan_loop(self):
        """扫描循环"""
        while True:
            try:
                await self._scan_devices()
                await asyncio.sleep(self._scan_interval)
            except Exception as e:
                logger.error(f"设备扫描失败: {str(e)}")
                await asyncio.sleep(5)

    async def _scan_devices(self):
        """扫描设备"""
        devices = usb_scanner.scan_devices()

        # 更新端口状态
        for device_id, device in devices.items():
            for port_number in device.port_numbers:
                if port_number not in self._port_status:
                    self._port_status[port_number] = PortStatus(
                        port_number=port_number, is_enabled=True
                    )

                port_status = self._port_status[port_number]
                port_status.current_device = device
                port_status.is_authorized = usb_scanner.is_device_authorized(device_id)

    async def enable_port(self, port_number: int) -> bool:
        """启用端口"""
        try:
            if port_number not in self._port_status:
                return False

            port_status = self._port_status[port_number]
            if not port_status.is_enabled:
                # 启用端口
                os.system(f"echo '1' > /sys/bus/usb/devices/{port_number}/authorized")
                port_status.is_enabled = True

            return True
        except Exception as e:
            logger.error(f"启用端口失败: {str(e)}")
            return False

    async def disable_port(self, port_number: int) -> bool:
        """禁用端口"""
        try:
            if port_number not in self._port_status:
                return False

            port_status = self._port_status[port_number]
            if port_status.is_enabled:
                # 禁用端口
                os.system(f"echo '0' > /sys/bus/usb/devices/{port_number}/authorized")
                port_status.is_enabled = False

            return True
        except Exception as e:
            logger.error(f"禁用端口失败: {str(e)}")
            return False

    def get_port_status(self, port_number: int) -> Optional[PortStatus]:
        """获取端口状态"""
        return self._port_status.get(port_number)

    def get_all_ports_status(self) -> Dict[int, PortStatus]:
        """获取所有端口状态"""
        return self._port_status.copy()


usb_controller = USBController()
