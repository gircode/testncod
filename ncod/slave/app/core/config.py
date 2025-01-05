"""
从服务器配置模块
"""

import secrets
from typing import Any, Dict, List, Optional
from pydantic import Field, PostgresDsn, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from ncod.core.key_manager import key_manager


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", env_prefix="NCOD_"
    )

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(default_factory=lambda: key_manager.get_key("SECRET_KEY"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # PostgreSQL配置
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = Field(
        default_factory=lambda: key_manager.get_key("DB_SLAVE_PASSWORD")
    )
    POSTGRES_DB: str = "ncod_slave"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        values = info.data
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = Field(
        default_factory=lambda: key_manager.get_key("REDIS_SLAVE_PASSWORD")
    )
    REDIS_URL: str = "redis://localhost:6379/0"

    # 监控配置
    MONITOR_INTERVAL: int = 60  # 监控间隔(秒)
    CPU_THRESHOLD: float = 80.0  # CPU告警阈值(%)
    MEMORY_THRESHOLD: float = 80.0  # 内存告警阈值(%)
    DISK_THRESHOLD: float = 80.0  # 磁盘告警阈值(%)
    NETWORK_THRESHOLD: float = 80.0  # 网络告警阈值(%)

    # 数据管理配置
    DATA_RETENTION_DAYS: int = 30


settings = Settings()
