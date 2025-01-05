"""数据库连接模块"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from ncod.utils.config import settings
from ncod.utils.logger import logger

# 创建异步引擎
engine = create_async_engine(
    settings.DB_URL,
    echo=settings.DEBUG,
    pool_size=settings.WORKER_PROCESSES * 2,
    max_overflow=10,
    pool_timeout=60,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# 创建异步会话工厂
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

# 创建基类
Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话

    Yields:
        AsyncSession: 异步数据库会话
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"数据库会话异常: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


# 创建异步会话上下文管理器
async_session = async_session_factory
