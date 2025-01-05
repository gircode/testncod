"""
Development configuration
"""

from pathlib import Path
from ncod.core.key_manager import key_manager

# 基础路径配置
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"

# 数据库配置
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": key_manager.get_key("DB_PASSWORD"),
    "database": "ncod_dev",
    "min_connections": 1,
    "max_connections": 10,
}

# Redis配置
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": key_manager.get_key("REDIS_PASSWORD"),
}

# 缓存配置
CACHE_CONFIG = {"type": "redis", "ttl": 300, "prefix": "ncod:"}  # 5分钟

# 日志配置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/ncod.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "standard",
            "level": "INFO",
        },
    },
    "loggers": {
        "": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": True}
    },
}

# 安全配置
SECURITY_CONFIG = {
    "secret_key": key_manager.get_key("SECRET_KEY"),
    "algorithm": "HS256",
    "access_token_expire_minutes": 30,
    "refresh_token_expire_days": 7,
    "password_hash_algorithm": "bcrypt",
    "password_min_length": 8,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 15,
}

# 性能监控配置
MONITOR_CONFIG = {
    "enabled": True,
    "interval": 5,  # 秒
    "history_size": 100,
    "metrics": ["cpu", "memory", "disk", "network"],
}

# 开发服务器配置
DEV_SERVER = {
    "host": "localhost",
    "port": 8000,
    "reload": True,
    "debug": True,
    "workers": 1,
}

# 模拟数据配置
MOCK_DATA = {
    "clusters": [
        {
            "id": "1",
            "name": "测试集群1",
            "status": "active",
            "node_count": 3,
            "last_heartbeat": "2024-03-20T10:00:00",
        },
        {
            "id": "2",
            "name": "测试集群2",
            "status": "inactive",
            "node_count": 2,
            "last_heartbeat": "2024-03-20T09:30:00",
        },
    ],
    "tasks": [
        {
            "id": "1",
            "name": "数据同步任务",
            "status": "running",
            "progress": 75,
            "created_at": "2024-03-20T08:00:00",
        }
    ],
    "performance": {
        "cpu_usage": [
            {"timestamp": "2024-03-20T09:00:00", "value": 45},
            {"timestamp": "2024-03-20T09:05:00", "value": 52},
            {"timestamp": "2024-03-20T09:10:00", "value": 48},
        ],
        "memory_usage": [
            {"timestamp": "2024-03-20T09:00:00", "value": 62},
            {"timestamp": "2024-03-20T09:05:00", "value": 65},
            {"timestamp": "2024-03-20T09:10:00", "value": 63},
        ],
    },
}
