"""
前端配置
"""

import os
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel, Field
from ncod.core.key_manager import key_manager


class Settings(BaseModel):
    """前端配置"""

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_prefix = "NCOD_"
        use_enum_values = True
        validate_assignment = True

    # API配置
    API_URL: str = os.getenv("API_URL", "http://localhost:8000")

    # 认证配置
    AUTH_COOKIE_NAME: str = os.getenv("AUTH_COOKIE_NAME", "access_token")
    SESSION_EXPIRE_MINUTES: int = int(os.getenv("SESSION_EXPIRE_MINUTES", "30"))
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: key_manager.get_key("JWT_SECRET_KEY")
    )

    # 主题配置
    THEME: Dict[str, Any] = {
        "primaryColor": "#1f77b4",
        "backgroundColor": "#ffffff",
        "secondaryBackgroundColor": "#f0f2f6",
        "textColor": "#31333F",
        "font": "sans-serif",
    }

    # 监控配置
    METRICS_REFRESH_INTERVAL: int = int(
        os.getenv("METRICS_REFRESH_INTERVAL", "30")
    )  # 秒
    ALERT_REFRESH_INTERVAL: int = int(os.getenv("ALERT_REFRESH_INTERVAL", "60"))  # 秒

    # 图表配置
    CHART_HEIGHT: int = int(os.getenv("CHART_HEIGHT", "400"))
    CHART_THEME: str = os.getenv("CHART_THEME", "plotly")

    # 缓存配置
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5分钟


settings = Settings()
