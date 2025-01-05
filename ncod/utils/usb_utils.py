"""USB设备管理工具"""

import os
import re
import pyudev
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ncod.utils.logger import logger
from ncod.core.cache import redis_client
from ncod.core.db import get_db_session
from ncod.models.device import AuthorizedDevice
from ncod.core.security import verify_device_signature


@dataclass
class USBDevice:
    """USB设备信息"""

    vendor_id: str
    product_id: str
    serial_number: Optional[str]
    manufacturer: Optional[str]
    product: Optional[str]
    port_numbers: List[int]
    bus_number: int
    device_address: int


class USBDeviceScanner:
    """USB设备扫描器"""

    def __init__(self):
        self.context = pyudev.Context()
        self._devices: Dict[str, USBDevice] = {}

    def scan_devices(self) -> Dict[str, USBDevice]:
        """扫描USB设备"""
        try:
            devices = {}
            for device in self.context.list_devices(
                subsystem="usb", DEVTYPE="usb_device"
            ):
                try:
                    if device.get("ID_VENDOR_ID") and device.get("ID_MODEL_ID"):
                        device_info = USBDevice(
                            vendor_id=device.get("ID_VENDOR_ID"),
                            product_id=device.get("ID_MODEL_ID"),
                            serial_number=device.get("ID_SERIAL_SHORT"),
                            manufacturer=device.get("ID_VENDOR_FROM_DATABASE"),
                            product=device.get("ID_MODEL_FROM_DATABASE"),
                            port_numbers=self._get_port_numbers(device),
                            bus_number=int(device.get("BUSNUM", 0)),
                            device_address=int(device.get("DEVNUM", 0)),
                        )
                        device_id = f"{device_info.vendor_id}:{device_info.product_id}"
                        if device_info.serial_number:
                            device_id += f":{device_info.serial_number}"
                        devices[device_id] = device_info
                except Exception as e:
                    logger.error(f"处理设备信息失败: {str(e)}")
                    continue

            self._devices = devices
            return devices
        except Exception as e:
            logger.error(f"扫描USB设备失败: {str(e)}")
            return {}

    def _get_port_numbers(self, device) -> List[int]:
        """获取端口号列表"""
        try:
            devpath = device.get("DEVPATH", "")
            port_numbers = []

            # 从设备路径中提取端口号
            port_match = re.findall(r"(\d+)-(\d+)(?:/\d+)*$", devpath)
            if port_match:
                port_numbers = [int(num) for num in port_match[0][1:]]

            return port_numbers
        except Exception as e:
            logger.error(f"获取端口号失败: {str(e)}")
            return []

    def get_device(self, device_id: str) -> Optional[USBDevice]:
        """获取设备信息"""
        return self._devices.get(device_id)

    def is_device_authorized(self, device_id: str) -> bool:
        """检查设备是否已授权

        Args:
            device_id: 设备ID，格式为 vendor_id:product_id[:serial_number]

        Returns:
            bool: 设备是否已授权
        """
        try:
            # 1. 先检查缓存
            cache_key = f"device_auth:{device_id}"
            cached_result = redis_client.get(cache_key)
            if cached_result is not None:
                return cached_result == "1"

            # 2. 获取设备信息
            device = self.get_device(device_id)
            if not device:
                self._log_auth_result(device_id, None, False, "设备未找到")
                return False

            # 3. 检查数据库中的授权记录
            with get_db_session() as session:
                auth_device = (
                    session.query(AuthorizedDevice)
                    .filter(
                        AuthorizedDevice.vendor_id == device.vendor_id,
                        AuthorizedDevice.product_id == device.product_id,
                    )
                    .first()
                )

                if not auth_device:
                    self._log_auth_result(
                        device_id, device, False, "设备未在授权列表中"
                    )
                    redis_client.setex(cache_key, 300, "0")  # 缓存5分钟
                    return False

                if not auth_device.is_active:
                    self._log_auth_result(device_id, device, False, "设备授权已禁用")
                    redis_client.setex(cache_key, 300, "0")
                    return False

                # 4. 如果设备有序列号，需要进行额外验证
                if device.serial_number:
                    if (
                        not auth_device.allow_any_serial
                        and device.serial_number != auth_device.serial_number
                    ):
                        self._log_auth_result(
                            device_id, device, False, "设备序列号不匹配"
                        )
                        redis_client.setex(cache_key, 300, "0")
                        return False

                    # 验证设备签名
                    if not verify_device_signature(device):
                        self._log_auth_result(
                            device_id, device, False, "设备签名验证失败"
                        )
                        redis_client.setex(cache_key, 300, "0")
                        return False

                # 5. 检查授权是否过期
                if auth_device.expire_time and auth_device.expire_time < datetime.now():
                    self._log_auth_result(device_id, device, False, "设备授权已过期")
                    redis_client.setex(cache_key, 300, "0")
                    return False

                # 6. 记录授权成功日志
                self._log_auth_result(device_id, device, True, "授权验证通过")

                # 7. 缓存结果
                redis_client.setex(cache_key, 300, "1")  # 缓存5分钟
                return True

        except Exception as e:
            logger.error(f"检查设备授权失败: {str(e)}")
            self._log_auth_result(device_id, None, False, f"授权检查异常: {str(e)}")
            return False

    def _log_auth_result(
        self,
        device_id: str,
        device: Optional[USBDevice],
        is_authorized: bool,
        reason: str,
    ):
        """记录授权检查结果

        Args:
            device_id: 设备ID
            device: USB设备对象
            is_authorized: 是否授权
            reason: 授权/拒绝原因
        """
        try:
            with get_db_session() as session:
                log = DeviceAuthLog(
                    device_id=device_id,
                    vendor_id=device.vendor_id if device else "",
                    product_id=device.product_id if device else "",
                    serial_number=device.serial_number if device else None,
                    manufacturer=device.manufacturer if device else None,
                    product=device.product if device else None,
                    is_authorized=is_authorized,
                    reason=reason,
                )
                session.add(log)
                session.commit()

                logger.info(
                    f"设备授权检查 - ID: {device_id}, "
                    f"厂商: {device.manufacturer if device else 'Unknown'}, "
                    f"产品: {device.product if device else 'Unknown'}, "
                    f"结果: {'通过' if is_authorized else '拒绝'}, "
                    f"原因: {reason}"
                )
        except Exception as e:
            logger.error(f"记录授权日志失败: {str(e)}")


class USBController:
    """USB设备控制器"""

    def __init__(self):
        self.sys_usb_path = Path("/sys/bus/usb/devices")

    def list_devices(self) -> List[Dict[str, str]]:
        """列出所有USB设备

        Returns:
            List[Dict[str, str]]: USB设备列表
        """
        devices = []
        if not self.sys_usb_path.exists():
            logger.warning("USB设备目录不存在")
            return devices

        for device_path in self.sys_usb_path.glob("*-*"):
            device_info = self._read_device_info(device_path)
            if device_info:
                devices.append(device_info)

        return devices

    def _read_device_info(self, device_path: Path) -> Optional[Dict[str, str]]:
        """读取USB设备信息

        Args:
            device_path: 设备路径

        Returns:
            Optional[Dict[str, str]]: 设备信息
        """
        try:
            # 读取设备ID
            idVendor = (device_path / "idVendor").read_text().strip()
            idProduct = (device_path / "idProduct").read_text().strip()

            # 读取制造商和产品信息
            manufacturer = self._read_file(device_path / "manufacturer")
            product = self._read_file(device_path / "product")
            serial = self._read_file(device_path / "serial")

            device_info = {
                "vendor_id": idVendor,
                "product_id": idProduct,
                "manufacturer": manufacturer,
                "product": product,
                "serial": serial,
                "path": str(device_path),
            }
            logger.debug(f"Found USB device: {device_info}")
            return device_info

        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"Error reading device info: {e}")
            return None

    def _read_file(self, path: Path) -> str:
        """安全读取文件内容

        Args:
            path: 文件路径

        Returns:
            str: 文件内容
        """
        try:
            return path.read_text().strip()
        except (FileNotFoundError, PermissionError):
            return ""

    def get_device_by_id(
        self, vendor_id: str, product_id: str
    ) -> Optional[Dict[str, str]]:
        """通过厂商ID和产品ID查找设备

        Args:
            vendor_id: 厂商ID
            product_id: 产品ID

        Returns:
            Optional[Dict[str, str]]: 设备信息
        """
        devices = self.list_devices()
        for device in devices:
            if device["vendor_id"] == vendor_id and device["product_id"] == product_id:
                return device
        return None

    def get_device_by_serial(self, serial: str) -> Optional[Dict[str, str]]:
        """通过序列号查找设备

        Args:
            serial: 设备序列号

        Returns:
            Optional[Dict[str, str]]: 设备信息
        """
        devices = self.list_devices()
        for device in devices:
            if device["serial"] == serial:
                return device
        return None


# 创建全局USB控制器实例
usb_controller = USBController()
