"""
配置模块
"""

import os
from typing import Any, Dict, Optional
from pydantic import BaseSettings, Field, computed_field
from ncod.core.key_manager import key_manager


class Settings(BaseSettings):
    """应用配置"""

    model_config = {"case_sensitive": True, "env_file": ".env", "env_prefix": "NCOD_"}

    PROJECT_NAME: str = "NCOD"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # 安全配置
    SECRET_KEY: str = Field(default_factory=lambda: key_manager.get_key("SECRET_KEY"))
    ALGORITHM: str = "HS256"

    # 数据库配置
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = Field(
        default_factory=lambda: key_manager.get_key("DB_MASTER_PASSWORD")
    )
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ncod")
    SQLALCHEMY_POOL_SIZE: int = int(os.getenv("SQLALCHEMY_POOL_SIZE", "5"))
    SQLALCHEMY_MAX_OVERFLOW: int = int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "10"))
    SQLALCHEMY_POOL_TIMEOUT: int = int(os.getenv("SQLALCHEMY_POOL_TIMEOUT", "30"))
    SQLALCHEMY_POOL_RECYCLE: int = int(os.getenv("SQLALCHEMY_POOL_RECYCLE", "1800"))

    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = Field(
        default_factory=lambda: key_manager.get_key("REDIS_MASTER_PASSWORD")
    )

    # 缓存配置
    CACHE_KEY_PREFIX: str = os.getenv("CACHE_KEY_PREFIX", "ncod:")
    CACHE_DEFAULT_TIMEOUT: int = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))
    USER_CACHE_TTL: int = int(os.getenv("USER_CACHE_TTL", "3600"))

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """数据库连接URI"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/"
            f"{self.POSTGRES_DB}"
        )


settings = Settings()
