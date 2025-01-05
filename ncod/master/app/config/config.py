"""应用配置模块"""

# 标准库导入
import os
from pathlib import Path
from typing import Any, Dict, Optional

# 第三方库导入
from pydantic import BaseModel, Field

# 本地导入
from ncod.core.key_manager import key_manager


class Settings(BaseModel):
    """应用配置类"""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "NCOD_"
        use_enum_values = True
        validate_assignment = True

    # 基础配置
    APP_NAME: str = "NCOD设备管理系统"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # API配置
    API_V1_STR: str = "/api/v1"
    API_URL: str = "http://localhost:8000"

    # 安全配置
    SECRET_KEY: str = Field(default_factory=lambda: key_manager.get_key("SECRET_KEY"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # 数据库配置
    DATABASE_URL: str = Field(
        default_factory=lambda: (
            f"postgresql+asyncpg://postgres:"
            f"{key_manager.get_key('DB_MASTER_PASSWORD')}@localhost:5432/ncod"
        )
    )

    # Redis配置
    REDIS_URL: str = Field(
        default_factory=lambda: (
            f"redis://:{key_manager.get_key('REDIS_MASTER_PASSWORD')}"
            "@localhost:6379/0"
        )
    )

    # 设备配置
    MAX_DEVICES: int = 1000
    DEVICE_SYNC_INTERVAL: int = 60  # 秒
    DEVICE_TIMEOUT: int = 300  # 秒

    # 监控配置
    ENABLE_MONITORING: bool = True
    METRICS_INTERVAL: int = 60  # 秒
    PROMETHEUS_PUSH_GATEWAY: Optional[str] = None

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: Path = Field(default_factory=lambda: Path("logs"), env="LOG_DIR")

    # 文件存储配置
    UPLOAD_DIR: Path = Field(default_factory=lambda: Path("uploads"), env="UPLOAD_DIR")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # 邮件配置
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Slack配置
    SLACK_API_TOKEN: Optional[str] = None


# 创建配置实例
settings = Settings()
