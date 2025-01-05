"""API测试"""

import pytest
from fastapi.testclient import TestClient
from ..app.main import app

client = TestClient(app)


def test_health_check():
    """测试健康检查接口"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "warning", "error"]


def test_metrics():
    """测试指标接口"""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "cpu_percent" in data
    assert "memory_percent" in data
    assert isinstance(data["cpu_percent"], float)
    assert isinstance(data["memory_percent"], float)


def test_alerts():
    """测试告警接口"""
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        alert = data[0]
        assert "severity" in alert
        assert "message" in alert
        assert "created_at" in alert


def test_device_status():
    """测试设备状态接口"""
    device_id = "test-device-1"
    response = client.get(f"/api/v1/devices/{device_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert "device_id" in data
    assert data["device_id"] == device_id
    assert "status" in data


def test_device_control():
    """测试设备控制接口"""
    device_id = "test-device-1"
    command = {"action": "restart"}
    response = client.post(f"/api/v1/devices/{device_id}/control", json=command)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["device_id"] == device_id
    assert data["action"] == "restart"
