"""日志模块"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(name: str) -> logging.Logger:
    """设置日志记录器"""
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 添加文件处理器
    file_handler = RotatingFileHandler(
        f"logs/{name}.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 创建主要的日志记录器
master_logger = setup_logger("master")

slave_logger = setup_logger("slave")

auth_logger = setup_logger("auth")

device_logger = setup_logger("device")

monitor_logger = setup_logger("monitor")
