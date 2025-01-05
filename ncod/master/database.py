from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from .config.settings import DATABASE_CONFIG

# 创建异步数据库引擎
db_url = f"postgresql+asyncpg://{DATABASE_CONFIG['default']['USER']}:{DATABASE_CONFIG['default']['PASSWORD']}@{DATABASE_CONFIG['default']['HOST']}:{DATABASE_CONFIG['default']['PORT']}/{DATABASE_CONFIG['default']['NAME']}"
engine = create_async_engine(
    db_url,
    pool_size=DATABASE_CONFIG["default"]["POOL_SIZE"],
    max_overflow=DATABASE_CONFIG["default"]["MAX_OVERFLOW"],
    echo=False,
)

# 创建异步会话工厂
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 创建全局会话管理器
async_session = async_session_factory
