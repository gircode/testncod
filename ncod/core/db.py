"""数据库管理模块"""

from typing import Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.pool import AsyncAdaptedQueuePool

from .config import settings
from ..utils.logger import logger


class Base(DeclarativeBase):
    """所有数据库Model的基类"""

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        """返回表名，将驼峰命名转换为下划线命名"""
        name = cls.__name__
        return "".join(
            ["_" + c.lower() if c.isupper() else c.lower() for c in name]
        ).lstrip("_")

    def to_dict(self) -> dict[str, Any]:
        """基础的字典转换方法"""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        # 构建数据库URL
        self.database_url = (
            f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )

        self.engine = create_async_engine(
            self.database_url,
            echo=settings.DEBUG,
            future=True,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
        )

        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self) -> None:
        """初始化数据库"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        async with self.async_session() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"数据库会话异常: {str(e)}")
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """关闭数据库连接"""
        try:
            await self.engine.dispose()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {str(e)}")
            raise


db = DatabaseManager()


def init_db() -> None:
    """初始化数据库"""
    import asyncio

    asyncio.run(db.init_db())
