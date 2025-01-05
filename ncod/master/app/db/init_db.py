"""
数据库初始化
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from .base_class import Base
from .session import engine

# 配置日志
logger = logging.getLogger(__name__)


async def init_db() -> None:
    """初始化数据库"""
    try:
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("数据库初始化完成")

    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise
