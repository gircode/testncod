"""设备API测试"""

import pytest
from fastapi import status
from ...models.device import Device


def test_get_devices(client, db):
    """测试获取设备列表"""
    response = client.get("/api/v1/devices")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "devices" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


def test_register_device(client, db):
    """测试注册设备"""
    response = client.post(
        "/api/v1/devices",
        json={
            "name": "Test Device",
            "mac_address": "00:11:22:33:44:55",
            "device_type": "test",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Device"
    assert data["mac_address"] == "00:11:22:33:44:55"
    assert data["device_type"] == "test"
