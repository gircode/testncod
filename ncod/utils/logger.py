"""日志模块"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from ncod.utils.config import settings


def setup_logger(name: str = "ncod", log_file: Optional[Path] = None) -> logging.Logger:
    """设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，如果为None则使用默认配置

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    logger.setLevel(settings.LOG_LEVEL.upper())

    # 创建格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 添加文件处理器
    log_path = log_file or settings.LOG_PATH
    if log_path:
        # 确保日志目录存在
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            str(log_path),  # 转换为字符串
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 创建全局日志记录器
logger = setup_logger(
    level=settings.LOG_LEVEL,
    log_file=settings.LOG_FILE,
    max_bytes=settings.LOG_MAX_BYTES,
    backup_count=settings.LOG_BACKUP_COUNT,
    fmt=settings.LOG_FORMAT,
)
