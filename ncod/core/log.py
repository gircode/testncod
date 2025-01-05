"""日志配置模块"""

import os
import logging
from logging.handlers import RotatingFileHandler


def configure_logging():
    """配置日志系统"""
    # 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 添加文件处理器到根日志记录器
    file_handler = RotatingFileHandler(
        "logs/ncod.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logging.getLogger().addHandler(file_handler)
