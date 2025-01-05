"""数据库工具模块"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ncod.utils.config import settings

# 创建异步数据库引擎
engine = create_async_engine(
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
    echo=settings.DEBUG,
    future=True,
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话

    Yields:
        AsyncSession: 异步数据库会话
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库"""
    from ncod.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
