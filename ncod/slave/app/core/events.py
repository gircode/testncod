"""
事件处理
"""

import logging
from typing import Callable

from fastapi import FastAPI

from ..db.session import engine
from ..models.base import Base
from .config import settings

logger = logging.getLogger(__name__)


async def startup_handler() -> None:
    """启动事件处理器"""
    try:
        # 创建数据库表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("数据库表创建成功")

        # 初始化其他资源
        # TODO: 添加其他初始化逻辑

    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        raise


async def shutdown_handler() -> None:
    """关闭事件处理器"""
    try:
        # 关闭数据库连接
        await engine.dispose()

        logger.info("数据库连接已关闭")

        # 清理其他资源
        # TODO: 添加其他清理逻辑

    except Exception as e:
        logger.error(f"关闭失败: {str(e)}")
        raise
