"""日志管理模块"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str, log_file: Optional[str] = None, level: int = logging.INFO
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件名，如果为None则只输出到控制台
        level: 日志级别

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path / log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 创建主要的日志记录器
master_logger = setup_logger("master", "master.log")
slave_logger = setup_logger("slave", "slave.log")
