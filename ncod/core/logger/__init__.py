"""日志管理模块"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict
from ncod.core.config import config

# 创建日志目录
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 日志格式
log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_file_handler(name: str) -> RotatingFileHandler:
    """获取文件处理器"""
    handler = RotatingFileHandler(
        log_dir / f"{name}.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(log_format)
    return handler


def get_console_handler() -> logging.StreamHandler:
    """获取控制台处理器"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_format)
    return handler


class LoggerManager:
    """日志管理器"""

    _loggers: Dict[str, logging.Logger] = {}

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """获取日志记录器"""
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(config.logging_config.get("level", logging.INFO))

            # 避免重复添加处理器
            if not logger.handlers:
                logger.addHandler(get_console_handler())
                logger.addHandler(get_file_handler(name))

            cls._loggers[name] = logger

        return cls._loggers[name]


# 创建主要的日志记录器
master_logger = LoggerManager.get_logger("master")
slave_logger = LoggerManager.get_logger("slave")
device_logger = LoggerManager.get_logger("device")
monitor_logger = LoggerManager.get_logger("monitor")
auth_logger = LoggerManager.get_logger("auth")
