"""日志工具模块"""

# 标准库导入
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 第三方库导入
from loguru import logger

# 日志格式
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    rotation: str = "1 day",
    retention: str = "30 days",
) -> None:
    """配置日志系统

    Args:
        level: 日志级别
        log_file: 日志文件路径
        rotation: 日志轮转策略
        retention: 日志保留策略
    """
    # 移除默认处理器
    logger.remove()

    # 添加控制台处理器
    logger.add(sys.stderr, format=LOG_FORMAT, level=level, colorize=True)

    # 添加文件处理器
    if log_file:
        logger.add(
            log_file,
            format=LOG_FORMAT,
            level=level,
            rotation=rotation,
            retention=retention,
            compression="zip",
        )


# 配置默认日志
setup_logging()
