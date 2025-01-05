import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
from ..config import Config

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """配置日志记录器"""
    # 创建日志目录
    os.makedirs(Config.LOG_PATH, exist_ok=True)
    
    # 如果未指定日志文件，使用默认配置
    if not log_file:
        log_file = os.path.join(Config.LOG_PATH, Config.LOG_FILENAME)
        
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(Config.LOG_LEVEL)
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(Config.LOG_LEVEL)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(Config.LOG_LEVEL)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """获取或创建日志记录器"""
    logger = logging.getLogger(name)
    
    # 如果日志记录器还没有处理器，则进行配置
    if not logger.handlers:
        return setup_logger(name)
        
    return logger

def log_error(logger: logging.Logger, error: Exception, message: str) -> None:
    """记录错误日志"""
    logger.error(f"{message}: {str(error)}", exc_info=True)

def log_warning(logger: logging.Logger, message: str) -> None:
    """记录警告日志"""
    logger.warning(message)

def log_info(logger: logging.Logger, message: str) -> None:
    """记录信息日志"""
    logger.info(message)

def log_debug(logger: logging.Logger, message: str) -> None:
    """记录调试日志"""
    logger.debug(message)
