"""设备服务测试"""

import pytest
from ...services.device import DeviceService
from ...core.errors.exceptions import ValidationError


def test_register_device(db):
    """测试注册设备"""
    device_service = DeviceService()
    device_data = {
        "name": "Test Device",
        "mac_address": "00:11:22:33:44:55",
        "device_type": "test",
    }
    device = device_service.register_device(db, user_id=1, device_data=device_data)
    assert device.name == device_data["name"]
    assert device.mac_address == device_data["mac_address"]
    assert device.device_type == device_data["device_type"]
    assert device.user_id == 1


def test_get_user_devices(db):
    """测试获取用户设备"""
    device_service = DeviceService()
    devices = device_service.get_user_devices(db, user_id=1)
    assert isinstance(devices, list)


def test_device_limit(db):
    """测试设备数量限制"""
    device_service = DeviceService()

    # 添加最大数量的设备
    for i in range(settings.MAX_DEVICES_PER_USER):
        device_data = {
            "name": f"Test Device {i}",
            "mac_address": f"00:11:22:33:44:{i:02x}",
            "device_type": "test",
        }
        device_service.register_device(db, user_id=1, device_data=device_data)

    # 尝试添加超出限制的设备
    with pytest.raises(ValidationError):
        device_data = {
            "name": "Extra Device",
            "mac_address": "00:11:22:33:44:ff",
            "device_type": "test",
        }
        device_service.register_device(db, user_id=1, device_data=device_data)
