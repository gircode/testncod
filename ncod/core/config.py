"""系统配置"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """系统配置类"""

    # 基础配置
    DEBUG: bool = False
    WORKER_PROCESSES: int = 4

    # 服务器配置
    MASTER_PORT: int = 8000
    SLAVE_PORT: int = 8001

    # 目录配置
    DATA_DIR: str = "data"
    LOG_DIR: str = "logs"
    DRIVER_DIR: str = "drivers"
    VH_INSTALL_DIR: str = "virtualhere"

    # 数据库配置
    DB_URL: str = "sqlite+aiosqlite:///ncod.db"

    # VirtualHere配置
    VH_CONFIG_PATH: str = "config/virtualhere.conf"
    VH_SERVER_HOST: str = "localhost"
    VH_SERVER_PORT: int = 7575

    # 设备配置
    DEVICE_TIMEOUT: int = 30
    DEVICE_CHECK_INTERVAL: int = 5

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_PATH: str = "logs/ncod.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # API配置
    API_RATE_LIMIT: int = 100

    # 资源配置
    RESOURCE_RETRY_INTERVAL: int = 5
    RESOURCE_TIMEOUT: int = 60
    RESOURCE_BATCH_SIZE: int = 10
    RESOURCE_PRIORITY_LEVELS: int = 5

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="allow"
    )


# 创建全局配置实例
config = Settings()
