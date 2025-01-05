"""
配置模块测试模块
"""

import json
import logging.config
import os
from pathlib import Path

import pytest

from ..config import (
    Config,
    DeviceConfig,
    LogConfig,
    MetricsConfig,
    RedisConfig,
    SecurityConfig,
)


@pytest.fixture
def config_file(temp_dir):
    """创建测试配置文件"""
    config_data = {
        "master_url": "http://test-master:8000",
        "slave_id": "test-slave-1",
        "host": "0.0.0.0",
        "port": 8001,
        "debug": True,
        "log": {
            "level": "DEBUG",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "logs/slave.log",
            "max_size": 5242880,
            "backup_count": 3,
        },
        "redis": {
            "url": "redis://localhost:6379/0",
            "max_connections": 20,
            "socket_timeout": 10,
            "socket_connect_timeout": 10,
            "retry_on_timeout": True,
        },
        "device": {
            "polling_interval": 30,
            "timeout": 3.0,
            "retry_count": 5,
            "max_devices": 500,
            "stale_threshold": 43200,
        },
        "metrics": {
            "collection_interval": 30,
            "retention_period": 604800,
            "max_points": 500,
            "export_format": "json",
        },
        "security": {
            "api_key": "test-api-key",
            "ssl_cert": "certs/server.crt",
            "ssl_key": "certs/server.key",
            "allowed_hosts": ["localhost", "127.0.0.1"],
            "cors_origins": ["http://localhost:3000"],
        },
    }

    config_path = temp_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config_data, f)
    return config_path


def test_load_config_from_env():
    """测试从环境变量加载配置"""
    # 设置测试环境变量
    os.environ["NCOD_SLAVE_ID"] = "env-slave"
    os.environ["NCOD_SLAVE_MASTER_URL"] = "http://env-master:8000"
    os.environ["NCOD_SLAVE_PORT"] = "8002"
    os.environ["NCOD_SLAVE_LOG_LEVEL"] = "INFO"
    os.environ["NCOD_SLAVE_REDIS_URL"] = "redis://env-redis:6379/0"
    os.environ["NCOD_SLAVE_DEVICE_POLLING_INTERVAL"] = "45"
    os.environ["NCOD_SLAVE_METRICS_MAX_POINTS"] = "750"
    os.environ["NCOD_SLAVE_SECURITY_API_KEY"] = "env-api-key"

    config = Config.load()

    assert config.slave_id == "env-slave"
    assert config.master_url == "http://env-master:8000"
    assert config.port == 8002
    assert config.log.level == "INFO"
    assert config.redis.url == "redis://env-redis:6379/0"
    assert config.device.polling_interval == 45
    assert config.metrics.max_points == 750
    assert config.security.api_key == "env-api-key"


def test_load_config_from_file(config_file):
    """测试从文件加载配置"""
    config = Config.load(str(config_file))

    assert config.slave_id == "test-slave-1"
    assert config.master_url == "http://test-master:8000"
    assert config.port == 8001
    assert config.debug is True

    # 验证日志配置
    assert config.log.level == "DEBUG"
    assert config.log.file == "logs/slave.log"
    assert config.log.max_size == 5242880
    assert config.log.backup_count == 3

    # 验证Redis配置
    assert config.redis.url == "redis://localhost:6379/0"
    assert config.redis.max_connections == 20
    assert config.redis.socket_timeout == 10
    assert config.redis.retry_on_timeout is True

    # 验证设备配置
    assert config.device.polling_interval == 30
    assert config.device.timeout == 3.0
    assert config.device.retry_count == 5
    assert config.device.max_devices == 500

    # 验证指标配置
    assert config.metrics.collection_interval == 30
    assert config.metrics.retention_period == 604800
    assert config.metrics.max_points == 500
    assert config.metrics.export_format == "json"

    # 验证安全配置
    assert config.security.api_key == "test-api-key"
    assert config.security.ssl_cert == "certs/server.crt"
    assert config.security.allowed_hosts == ["localhost", "127.0.0.1"]
    assert config.security.cors_origins == ["http://localhost:3000"]


def test_save_config(temp_dir):
    """测试保存配置"""
    config = Config(
        slave_id="save-test-slave",
        master_url="http://save-test-master:8000",
        port=8003,
        debug=True,
        log=LogConfig(level="DEBUG", file="logs/test.log"),
        redis=RedisConfig(url="redis://save-test-redis:6379/0", max_connections=15),
        device=DeviceConfig(polling_interval=40, timeout=4.0),
        metrics=MetricsConfig(collection_interval=40, max_points=600),
        security=SecurityConfig(api_key="save-test-key", allowed_hosts=["localhost"]),
    )

    save_path = temp_dir / "saved_config.json"
    config.save(str(save_path))

    # 验证保存的文件
    assert save_path.exists()
    with open(save_path) as f:
        saved_data = json.load(f)

    assert saved_data["slave_id"] == "save-test-slave"
    assert saved_data["master_url"] == "http://save-test-master:8000"
    assert saved_data["port"] == 8003
    assert saved_data["debug"] is True
    assert saved_data["log"]["level"] == "DEBUG"
    assert saved_data["redis"]["url"] == "redis://save-test-redis:6379/0"
    assert saved_data["device"]["polling_interval"] == 40
    assert saved_data["metrics"]["max_points"] == 600
    assert saved_data["security"]["api_key"] == "save-test-key"


def test_setup_logging(temp_dir):
    """测试日志设置"""
    config = Config(
        slave_id="test-slave",
        log=LogConfig(
            level="DEBUG",
            file=str(temp_dir / "test.log"),
            format="%(levelname)s: %(message)s",
        ),
    )

    config.setup_logging()

    # 验证日志配置
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 2  # 控制台和文件处理器

    # 验证文件处理器
    file_handler = next(
        h
        for h in root_logger.handlers
        if isinstance(h, logging.handlers.RotatingFileHandler)
    )
    assert file_handler.baseFilename == str(temp_dir / "test.log")


def test_config_validation():
    """测试配置验证"""
    # 测试必需字段
    with pytest.raises(ValueError):
        Config()  # slave_id是必需的

    # 测试字段类型验证
    with pytest.raises(ValueError):
        Config(slave_id="test", port="invalid")  # 应该是整数

    # 测试嵌套配置验证
    with pytest.raises(ValueError):
        Config(slave_id="test", device=DeviceConfig(polling_interval=-1))  # 不能是负数


def test_config_defaults():
    """测试配置默认值"""
    config = Config(slave_id="test-slave")

    assert config.host == "0.0.0.0"
    assert config.port == 8001
    assert config.debug is False
    assert config.log.level == "INFO"
    assert config.redis.max_connections == 10
    assert config.device.retry_count == 3
    assert config.metrics.export_format == "prometheus"
    assert config.security.allowed_hosts == ["*"]


def test_environment_override(config_file):
    """测试环境变量覆盖配置文件"""
    # 设置环境变量
    os.environ["NCOD_SLAVE_PORT"] = "9000"
    os.environ["NCOD_SLAVE_LOG_LEVEL"] = "WARNING"
    os.environ["NCOD_SLAVE_REDIS_URL"] = "redis://override:6379/0"

    config = Config.load(str(config_file))

    # 环境变量应该覆盖配置文件的值
    assert config.port == 9000
    assert config.log.level == "WARNING"
    assert config.redis.url == "redis://override:6379/0"

    # 配置文件中的其他值应该保持不变
    assert config.slave_id == "test-slave-1"
    assert config.device.polling_interval == 30
