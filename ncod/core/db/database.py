"""数据库连接模块"""

from typing import AsyncGenerator, AsyncContextManager
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from ncod.core.config import config
from ncod.core.logger import setup_logger

logger = setup_logger("database")

# 创建异步引擎
engine = create_async_engine(
    config.database.url,
    echo=config.database.echo,
    pool_size=config.database.pool_size,
    max_overflow=config.database.max_overflow,
    pool_pre_ping=True,
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


class Base(DeclarativeBase):
    """声明性基类"""

    pass


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def close_db() -> None:
    """关闭数据库连接"""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise
