"""配置模块"""

from pathlib import Path
from typing import Dict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    # 基础配置
    DEBUG: bool = False
    WORKER_PROCESSES: int = 4

    # 目录配置
    DATA_DIR: Path = Path("data")
    LOG_DIR: Path = Path("logs")
    DRIVER_DIR: Path = Path("drivers")
    VH_INSTALL_DIR: Path = Path("virtualhere")

    # 资源配置
    RESOURCE_RETRY_INTERVAL: int = 5  # 资源分配重试间隔(秒)
    RESOURCE_TIMEOUT: int = 60  # 资源分配超时时间(秒)
    RESOURCE_BATCH_SIZE: int = 10  # 资源批量处理大小
    RESOURCE_PRIORITY_LEVELS: int = 5  # 资源优先级级别数
    RESOURCE_SCORE_WEIGHTS: Dict[str, float] = {  # 资源评分权重
        "cpu": 0.3,
        "memory": 0.3,
        "network": 0.2,
        "storage": 0.2,
    }

    # VirtualHere 配置
    VH_CONFIG_PATH: Path = Path("config/virtualhere.conf")
    VH_SERVER_HOST: str = "localhost"
    VH_SERVER_PORT: int = 7575

    # 设备监控配置
    DEVICE_TIMEOUT: int = 30  # 设备超时时间(秒)
    DEVICE_CHECK_INTERVAL: int = 5  # 设备状态检查间隔(秒)

    # 数据库配置
    DB_URL: str = "sqlite+aiosqlite:///ncod.db"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_PATH: Path = Path("logs/ncod.log")  # 改名以避免重复
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # API配置
    API_RATE_LIMIT: int = 100  # 每分钟请求数限制

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保必要的目录存在
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.DRIVER_DIR.mkdir(parents=True, exist_ok=True)
        self.VH_INSTALL_DIR.mkdir(parents=True, exist_ok=True)


# 创建全局配置实例
settings = Settings()
