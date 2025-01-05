"""
从服务器测试模块
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from ..app import App
from ..device_manager import DeviceConfig, DeviceStatus
from ..metrics_collector import Metric, MetricValue


@pytest.fixture
def app():
    """创建测试应用"""
    return App()


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app.app)


@pytest.fixture
def mock_device_manager():
    """模拟设备管理器"""
    with patch("ncod.slave.app.DeviceManager") as mock:
        manager = Mock()
        manager.get_all_devices.return_value = {
            "device1": DeviceConfig(
                id="device1",
                name="Test Device 1",
                type="http",
                address="localhost",
                port=8080,
                protocol="http",
                polling_interval=60,
                timeout=5.0,
                retry_count=3,
            )
        }
        manager.get_all_device_status.return_value = {
            "device1": DeviceStatus(
                id="device1",
                online=True,
                last_seen=datetime.now(),
                error_message=None,
                metrics={"response_time": 0.1},
            )
        }
        mock.return_value = manager
        yield manager


@pytest.fixture
def mock_metrics_collector():
    """模拟指标采集器"""
    with patch("ncod.slave.app.MetricsCollector") as mock:
        collector = Mock()
        collector.export_metrics.return_value = {
            "system_cpu_usage": {
                "type": "gauge",
                "description": "System CPU usage percentage",
                "unit": "percent",
                "values": [
                    {
                        "value": 50.0,
                        "timestamp": datetime.now().isoformat(),
                        "labels": None,
                    }
                ],
            }
        }
        mock.return_value = collector
        yield collector


def test_health_check(client):
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_get_metrics(client, app, mock_metrics_collector):
    """测试获取指标接口"""
    # 启动应用以初始化指标采集器
    await app.start()

    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "system_cpu_usage" in data
    assert data["system_cpu_usage"]["type"] == "gauge"
    assert len(data["system_cpu_usage"]["values"]) > 0

    # 停止应用
    await app.stop()


@pytest.mark.asyncio
async def test_get_devices(client, app, mock_device_manager):
    """测试获取设备列表接口"""
    # 启动应用以初始化设备管理器
    await app.start()

    response = client.get("/devices")
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert "statuses" in data
    assert len(data["devices"]) == 1
    assert "device1" in data["devices"]
    assert data["devices"]["device1"]["name"] == "Test Device 1"

    # 停止应用
    await app.stop()


@pytest.mark.asyncio
async def test_get_device(client, app, mock_device_manager):
    """测试获取单个设备接口"""
    # 启动应用以初始化设备管理器
    await app.start()

    response = client.get("/devices/device1")
    assert response.status_code == 200
    data = response.json()
    assert "device" in data
    assert "status" in data
    assert data["device"]["name"] == "Test Device 1"
    assert data["status"]["online"] is True

    # 测试不存在的设备
    response = client.get("/devices/nonexistent")
    assert response.status_code == 404

    # 停止应用
    await app.stop()


@pytest.mark.asyncio
async def test_add_device(client, app, mock_device_manager):
    """测试添加设备接口"""
    # 启动应用以初始化设备管理器
    await app.start()

    # 模拟设备管理器的add_device方法
    mock_device_manager.add_device.return_value = "new_device"

    device_data = {
        "name": "New Device",
        "type": "http",
        "address": "localhost",
        "port": 8080,
        "protocol": "http",
        "polling_interval": 60,
        "timeout": 5.0,
        "retry_count": 3,
        "custom_config": None,
    }

    response = client.post("/devices", json=device_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "new_device"

    # 测试无效的设备数据
    invalid_data = {
        "name": "Invalid Device"
        # 缺少必需字段
    }
    response = client.post("/devices", json=invalid_data)
    assert response.status_code == 422

    # 停止应用
    await app.stop()


@pytest.mark.asyncio
async def test_update_device(client, app, mock_device_manager):
    """测试更新设备接口"""
    # 启动应用以初始化设备管理器
    await app.start()

    device_data = {
        "name": "Updated Device",
        "type": "http",
        "address": "localhost",
        "port": 8080,
        "protocol": "http",
        "polling_interval": 60,
        "timeout": 5.0,
        "retry_count": 3,
        "custom_config": None,
    }

    response = client.put("/devices/device1", json=device_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # 测试更新不存在的设备
    mock_device_manager.update_device.side_effect = Exception("Device not found")
    response = client.put("/devices/nonexistent", json=device_data)
    assert response.status_code == 400

    # 停止应用
    await app.stop()


@pytest.mark.asyncio
async def test_delete_device(client, app, mock_device_manager):
    """测试删除设备接口"""
    # 启动应用以初始化设备管理器
    await app.start()

    response = client.delete("/devices/device1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # 测试删除不存在的设备
    mock_device_manager.delete_device.side_effect = Exception("Device not found")
    response = client.delete("/devices/nonexistent")
    assert response.status_code == 400

    # 停止应用
    await app.stop()


@pytest.mark.asyncio
async def test_test_device(client, app, mock_device_manager):
    """测试设备连接测试接口"""
    # 启动应用以初始化设备管理器
    await app.start()

    # 模拟设备测试结果
    mock_device_manager.test_device_connection.return_value = (True, None)

    response = client.post("/devices/device1/test")
    assert response.status_code == 200
    data = response.json()
    assert data["online"] is True
    assert data["error"] is None

    # 测试不存在的设备
    response = client.post("/devices/nonexistent/test")
    assert response.status_code == 404

    # 测试连接失败的情况
    mock_device_manager.test_device_connection.return_value = (
        False,
        "Connection failed",
    )
    response = client.post("/devices/device1/test")
    assert response.status_code == 200
    data = response.json()
    assert data["online"] is False
    assert data["error"] == "Connection failed"

    # 停止应用
    await app.stop()


@pytest.mark.asyncio
async def test_app_lifecycle(app, mock_device_manager, mock_metrics_collector):
    """测试应用生命周期"""
    # 测试启动
    await app.start()
    assert app.device_manager is not None
    assert app.metrics_collector is not None
    mock_device_manager.start.assert_called_once()
    mock_metrics_collector.start.assert_called_once()

    # 测试停止
    await app.stop()
    mock_device_manager.stop.assert_called_once()
    mock_metrics_collector.stop.assert_called_once()
