from pathlib import Path
import os
from typing import Dict, Any

# 基础路径配置
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据库配置
DATABASE_CONFIG = {
    "default": {
        "ENGINE": "postgresql",
        "NAME": os.getenv("DB_NAME", "ncod"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "POOL_SIZE": 20,
        "MAX_OVERFLOW": 10,
    }
}

# Redis缓存配置
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
    "password": os.getenv("REDIS_PASSWORD", None),
}

# WebSocket配置
WEBSOCKET_CONFIG = {
    "host": "0.0.0.0",
    "port": int(os.getenv("WS_PORT", 8765)),
    "path": "/ws",
    "ping_interval": 30,
    "ping_timeout": 10,
}

# 日志配置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/ncod.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
        },
    },
    "loggers": {
        "": {"handlers": ["default", "file"], "level": "INFO", "propagate": True},
    },
}

# 安全配置
SECURITY_CONFIG = {
    "jwt_secret": os.getenv("JWT_SECRET", "your-secret-key"),
    "jwt_algorithm": "HS256",
    "jwt_expiration": 3600,  # 1小时
    "password_hash_rounds": 12,
}

# VirtualHere配置
VIRTUALHERE_CONFIG = {
    "server_path": os.getenv("VH_SERVER_PATH", "/usr/bin/vhusbd"),
    "client_path": os.getenv("VH_CLIENT_PATH", "/usr/bin/vhclient"),
    "license_key": os.getenv("VH_LICENSE_KEY", ""),
    "auto_start": True,
    "monitor_interval": 5,  # 秒
}

# 设备监控配置
MONITORING_CONFIG = {
    "collect_interval": 30,  # 秒
    "retention_days": 30,
    "alert_threshold": {
        "cpu_usage": 80,  # CPU使用率阈值
        "memory_usage": 80,  # 内存使用率阈值
        "disk_usage": 90,  # 磁盘使用率阈值
    },
}

# 用户管理配置
USER_CONFIG = {
    "require_approval": True,
    "max_devices_per_user": 5,
    "session_timeout": 3600,  # 1小时
    "password_policy": {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special_chars": True,
    },
}

# 主从服务器配置
MASTER_SLAVE_CONFIG = {
    "heartbeat_interval": 10,  # 秒
    "slave_timeout": 30,  # 秒
    "auto_failover": True,
    "sync_interval": 300,  # 5分钟
}

# API配置
API_CONFIG = {
    "rate_limit": {
        "default": "100/minute",
        "auth": "10/minute",
    },
    "cors_origins": ["*"],
    "max_request_size": "10MB",
}
