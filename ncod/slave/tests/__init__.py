"""
NCOD从服务器测试包
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 测试常量
TEST_SLAVE_ID = "test_slave"
TEST_MASTER_URL = "http://master:8000"
TEST_HOST = "localhost"
TEST_PORT = 8001

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "data"
if not TEST_DATA_DIR.exists():
    TEST_DATA_DIR.mkdir(parents=True)

# 测试设备配置
TEST_DEVICE_CONFIG = {
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

# 测试指标数据
TEST_METRICS_DATA = {
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

# 测试配置数据
TEST_CONFIG_DATA = {
    "master_url": TEST_MASTER_URL,
    "slave_id": TEST_SLAVE_ID,
    "host": TEST_HOST,
    "port": TEST_PORT,
    "debug": True,
    "log": {
        "level": "DEBUG",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "logs/test.log",
        "max_size": 1048576,
        "backup_count": 3,
    },
    "redis": {
        "url": "redis://localhost:6379/0",
        "max_connections": 10,
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
        "retry_on_timeout": True,
    },
    "device": {
        "polling_interval": 30,
        "timeout": 3.0,
        "retry_count": 3,
        "max_devices": 100,
        "stale_threshold": 3600,
    },
    "metrics": {
        "collection_interval": 30,
        "retention_period": 86400,
        "max_points": 100,
        "export_format": "prometheus",
    },
    "security": {
        "api_key": "test-api-key",
        "ssl_cert": None,
        "ssl_key": None,
        "allowed_hosts": ["*"],
        "cors_origins": ["*"],
    },
}

# 测试响应数据
TEST_RESPONSES = {
    "health_check": {"status": "healthy"},
    "device_status": {
        "online": True,
        "last_seen": "2023-01-01T00:00:00",
        "error_message": None,
        "metrics": {"response_time": 0.1, "cpu_usage": 50.0, "memory_usage": 75.0},
    },
    "error": {"status": "error", "message": "Test error message", "code": "TEST_ERROR"},
}


# 测试工具函数
def create_test_config_file(path: Path, data: dict = None) -> Path:
    """创建测试配置文件"""
    import json

    if data is None:
        data = TEST_CONFIG_DATA

    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)

    return config_path


def cleanup_test_files(paths: list[Path]) -> None:
    """清理测试文件"""
    for path in paths:
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil

                shutil.rmtree(path)
        except Exception as e:
            print(f"Error cleaning up {path}: {e}")


# 测试装饰器
def requires_redis(func):
    """需要Redis的测试装饰器"""
    import aioredis
    import pytest

    async def check_redis():
        try:
            redis = await aioredis.from_url("redis://localhost")
            await redis.ping()
            await redis.close()
            return True
        except Exception:
            return False

    return pytest.mark.skipif(
        not pytest.asyncio.run(check_redis()), reason="Redis is not available"
    )(func)


def requires_master(func):
    """需要主服务器的测试装饰器"""
    import aiohttp
    import pytest

    async def check_master():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{TEST_MASTER_URL}/health") as resp:
                    return resp.status == 200
        except Exception:
            return False

    return pytest.mark.skipif(
        not pytest.asyncio.run(check_master()), reason="Master server is not available"
    )(func)
