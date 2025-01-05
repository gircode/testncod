"""
设备管理器测试模块
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from ..device_manager import DeviceConfig, DeviceManager, DeviceStatus


@pytest.fixture
def device_config():
    """创建测试设备配置"""
    return DeviceConfig(
        id="test_device",
        name="Test Device",
        type="http",
        address="localhost",
        port=8080,
        protocol="http",
        polling_interval=60,
        timeout=5.0,
        retry_count=3,
    )


@pytest.fixture
def mock_session():
    """模拟HTTP会话"""
    with patch("aiohttp.ClientSession") as mock:
        session = AsyncMock()
        mock.return_value = session
        yield session


@pytest.fixture
async def device_manager(mock_session):
    """创建设备管理器"""
    manager = DeviceManager(master_url="http://master:8000", slave_id="test_slave")
    manager._session = mock_session
    yield manager
    await manager.stop()


@pytest.mark.asyncio
async def test_start_stop(device_manager, mock_session):
    """测试启动和停止"""
    # 模拟从主服务器获取设备配置
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = []
    mock_session.get.return_value.__aenter__.return_value = mock_response

    # 测试启动
    await device_manager.start()
    mock_session.get.assert_called_once_with(
        "http://master:8000/api/slaves/test_slave/devices"
    )

    # 测试停止
    await device_manager.stop()
    assert not device_manager._polling_tasks


@pytest.mark.asyncio
async def test_sync_devices(device_manager, mock_session, device_config):
    """测试设备同步"""
    # 模拟从主服务器获取设备配置
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = [device_config.__dict__]
    mock_session.get.return_value.__aenter__.return_value = mock_response

    await device_manager._sync_devices_from_master()

    assert "test_device" in device_manager.devices
    assert device_manager.devices["test_device"].name == "Test Device"
    assert "test_device" in device_manager._polling_tasks


@pytest.mark.asyncio
async def test_poll_http_device(device_manager, mock_session, device_config):
    """测试HTTP设备轮询"""
    # 模拟成功的HTTP响应
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"status": "ok"}
    mock_session.get.return_value.__aenter__.return_value = mock_response

    online, error, metrics = await device_manager._poll_http_device(device_config)
    assert online is True
    assert error is None
    assert metrics == {"status": "ok"}

    # 模拟失败的HTTP响应
    mock_response.status = 500
    online, error, metrics = await device_manager._poll_http_device(device_config)
    assert online is False
    assert error == "HTTP status: 500"
    assert metrics == {}

    # 模拟连接超时
    mock_session.get.side_effect = aiohttp.ClientTimeout
    online, error, metrics = await device_manager._poll_http_device(device_config)
    assert online is False
    assert error == "Request timeout"
    assert metrics == {}


@pytest.mark.asyncio
async def test_poll_tcp_device(device_manager, device_config):
    """测试TCP设备轮询"""
    with patch("asyncio.open_connection") as mock_open_connection:
        # 模拟成功的TCP连接
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_reader.read.return_value = b"status: ok\n"
        mock_open_connection.return_value = (mock_reader, mock_writer)

        online, error, metrics = await device_manager._poll_tcp_device(device_config)
        assert online is True
        assert error is None
        assert metrics == {"raw_data": "status: ok\n"}

        # 模拟连接失败
        mock_open_connection.side_effect = ConnectionRefusedError
        online, error, metrics = await device_manager._poll_tcp_device(device_config)
        assert online is False
        assert "Connection refused" in error
        assert metrics == {}


@pytest.mark.asyncio
async def test_device_status_reporting(device_manager, mock_session, device_config):
    """测试设备状态上报"""
    # 模拟设备状态
    device_manager.device_status[device_config.id] = DeviceStatus(
        id=device_config.id,
        online=True,
        last_seen=datetime.now(),
        error_message=None,
        metrics={"response_time": 0.1},
    )

    # 模拟成功的状态上报
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_session.post.return_value.__aenter__.return_value = mock_response

    await device_manager._report_device_status(device_config.id)
    mock_session.post.assert_called_once()

    # 模拟失败的状态上报
    mock_response.status = 500
    await device_manager._report_device_status(device_config.id)
    assert mock_session.post.call_count == 2


@pytest.mark.asyncio
async def test_add_device(device_manager, mock_session, device_config):
    """测试添加设备"""
    # 模拟成功添加设备
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"id": "new_device"}
    mock_session.post.return_value.__aenter__.return_value = mock_response

    device_id = await device_manager.add_device(device_config.__dict__)
    assert device_id == "new_device"
    mock_session.post.assert_called_once()

    # 模拟添加设备失败
    mock_response.status = 400
    with pytest.raises(Exception):
        await device_manager.add_device(device_config.__dict__)


@pytest.mark.asyncio
async def test_update_device(device_manager, mock_session, device_config):
    """测试更新设备"""
    # 模拟成功更新设备
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_session.put.return_value.__aenter__.return_value = mock_response

    await device_manager.update_device(device_config.id, device_config.__dict__)
    mock_session.put.assert_called_once()

    # 模拟更新设备失败
    mock_response.status = 404
    with pytest.raises(Exception):
        await device_manager.update_device(device_config.id, device_config.__dict__)


@pytest.mark.asyncio
async def test_delete_device(device_manager, mock_session, device_config):
    """测试删除设备"""
    # 模拟成功删除设备
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_session.delete.return_value.__aenter__.return_value = mock_response

    await device_manager.delete_device(device_config.id)
    mock_session.delete.assert_called_once()

    # 模拟删除设备失败
    mock_response.status = 404
    with pytest.raises(Exception):
        await device_manager.delete_device(device_config.id)


@pytest.mark.asyncio
async def test_test_device_connection(device_manager, device_config):
    """测试设备连接测试"""
    # 测试HTTP设备
    with patch.object(device_manager, "_poll_http_device") as mock_http:
        mock_http.return_value = (True, None, {})
        online, error = await device_manager.test_device_connection(device_config)
        assert online is True
        assert error is None

        mock_http.return_value = (False, "Connection failed", {})
        online, error = await device_manager.test_device_connection(device_config)
        assert online is False
        assert error == "Connection failed"

    # 测试TCP设备
    device_config.protocol = "tcp"
    with patch.object(device_manager, "_poll_tcp_device") as mock_tcp:
        mock_tcp.return_value = (True, None, {})
        online, error = await device_manager.test_device_connection(device_config)
        assert online is True
        assert error is None

        mock_tcp.return_value = (False, "Connection refused", {})
        online, error = await device_manager.test_device_connection(device_config)
        assert online is False
        assert error == "Connection refused"

    # 测试不支持的协议
    device_config.protocol = "unknown"
    online, error = await device_manager.test_device_connection(device_config)
    assert online is False
    assert "Unsupported protocol" in error
