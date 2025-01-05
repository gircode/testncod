"""
Pytest配置文件
"""

import logging
import os
from pathlib import Path

import pytest

# 设置测试环境变量
os.environ.setdefault("NCOD_SLAVE_ID", "test_slave")
os.environ.setdefault("NCOD_SLAVE_MASTER_URL", "http://master:8000")
os.environ.setdefault("NCOD_SLAVE_HOST", "localhost")
os.environ.setdefault("NCOD_SLAVE_PORT", "8001")
os.environ.setdefault("NCOD_SLAVE_LOG_LEVEL", "DEBUG")

# 配置日志
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@pytest.fixture(scope="session")
def test_dir():
    """测试目录"""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def temp_dir(tmp_path_factory):
    """临时目录"""
    return tmp_path_factory.mktemp("test_data")


@pytest.fixture(autouse=True)
def setup_test_env():
    """设置测试环境"""
    # 保存原始环境变量
    original_env = {}
    test_env = {
        "NCOD_SLAVE_ID": "test_slave",
        "NCOD_SLAVE_MASTER_URL": "http://master:8000",
        "NCOD_SLAVE_HOST": "localhost",
        "NCOD_SLAVE_PORT": "8001",
        "NCOD_SLAVE_LOG_LEVEL": "DEBUG",
        "NCOD_SLAVE_REDIS_URL": "redis://localhost",
        "NCOD_SLAVE_DEVICE_POLLING_INTERVAL": "10",
        "NCOD_SLAVE_DEVICE_TIMEOUT": "5",
        "NCOD_SLAVE_DEVICE_RETRY_COUNT": "3",
        "NCOD_SLAVE_METRICS_COLLECTION_INTERVAL": "10",
        "NCOD_SLAVE_METRICS_MAX_POINTS": "100",
    }

    # 设置测试环境变量
    for key, value in test_env.items():
        if key in os.environ:
            original_env[key] = os.environ[key]
        os.environ[key] = value

    yield

    # 恢复原始环境变量
    for key in test_env:
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            del os.environ[key]


@pytest.fixture
def sample_device_config():
    """示例设备配置"""
    return {
        "name": "Test Device",
        "type": "http",
        "address": "localhost",
        "port": 8080,
        "protocol": "http",
        "polling_interval": 60,
        "timeout": 5.0,
        "retry_count": 3,
        "custom_config": {
            "path": "/status",
            "method": "GET",
            "headers": {"Content-Type": "application/json"},
        },
    }


@pytest.fixture
def sample_metrics_data():
    """示例指标数据"""
    return {
        "system_cpu_usage": {
            "type": "gauge",
            "description": "System CPU usage percentage",
            "unit": "percent",
            "values": [
                {
                    "value": 50.0,
                    "timestamp": "2023-01-01T00:00:00",
                    "labels": {"cpu": "total"},
                }
            ],
        },
        "system_memory_usage": {
            "type": "gauge",
            "description": "System memory usage percentage",
            "unit": "percent",
            "values": [
                {
                    "value": 75.0,
                    "timestamp": "2023-01-01T00:00:00",
                    "labels": {"type": "physical"},
                }
            ],
        },
    }


@pytest.fixture
def mock_config_file(temp_dir):
    """模拟配置文件"""
    config_data = {
        "master_url": "http://master:8000",
        "slave_id": "test_slave",
        "host": "localhost",
        "port": 8001,
        "log": {
            "level": "DEBUG",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "redis": {"url": "redis://localhost", "max_connections": 10},
        "device": {"polling_interval": 60, "timeout": 5.0, "retry_count": 3},
        "metrics": {"collection_interval": 60, "max_points": 1000},
    }

    config_file = temp_dir / "config.json"
    config_file.write_text(str(config_data))
    return config_file
