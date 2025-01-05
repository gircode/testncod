"""日志管理模块"""

import os
import logging
from typing import Dict, Any, Optional, cast
from logging import Logger as ExtendedLogger


class JsonFormatter(logging.Formatter):
    """JSON格式日志格式化器"""

    def __init__(self, **kwargs):
        self.extra_fields = kwargs
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加额外字段
        if hasattr(record, "extra_fields"):
            data.update(record.extra_fields)

        # 添加异常信息
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)

        # 添加自定义字段
        data.update(self.extra_fields)

        return str(data)


class LogManager:
    """日志管理器"""

    def __init__(
        self,
        log_dir: str = "logs",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        self.log_dir = log_dir
        self.console_level = console_level
        self.file_level = file_level
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.extra_fields = extra_fields or {}

        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)

        # 配置根日志器
        self.configure_root_logger()

    def configure_root_logger(self) -> None:
        """配置根日志器"""
        root_logger = cast(ExtendedLogger, logging.getLogger())
        root_logger.setLevel(logging.DEBUG)

        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.console_level)
        console_handler.setFormatter(JsonFormatter(**self.extra_fields))
        root_logger.addHandler(console_handler)

        # 添加文件处理器
        try:
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                filename=os.path.join(self.log_dir, "app.log"),
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(self.file_level)
            file_handler.setFormatter(JsonFormatter(**self.extra_fields))
            root_logger.addHandler(file_handler)

            # 添加错误日志处理器
            error_handler = RotatingFileHandler(
                filename=os.path.join(self.log_dir, "error.log"),
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(JsonFormatter(**self.extra_fields))
            root_logger.addHandler(error_handler)
        except ImportError:
            root_logger.warning(
                "RotatingFileHandler not available, falling back to basic file logging"
            )
            file_handler = logging.FileHandler(
                filename=os.path.join(self.log_dir, "app.log"), encoding="utf-8"
            )
            file_handler.setLevel(self.file_level)
            file_handler.setFormatter(JsonFormatter(**self.extra_fields))
            root_logger.addHandler(file_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """获取命名日志器"""
        return logging.getLogger(name)


log_manager = LogManager()
