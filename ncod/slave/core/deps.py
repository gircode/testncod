"""从服务器依赖管理"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from ncod.slave.device.manager import DeviceManager
from ncod.slave.device.controller import DeviceController

# 创建全局实例
device_manager = DeviceManager()
device_controller = DeviceController(device_manager)


async def get_device_manager() -> DeviceManager:
    """获取设备管理器"""
    return device_manager


async def get_device_controller() -> DeviceController:
    """获取设备控制器"""
    return device_controller
