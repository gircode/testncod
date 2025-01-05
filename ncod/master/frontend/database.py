"""Database模块"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings

settings = get_settings()

# 创建异步引擎
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# 创建会话工厂
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 创建基类
Base = declarative_base()


class Database:
    def __init__(self):
        self.engine = engine
        self.session_factory = async_session

    async def connect(self):
        """连接数据库"""
        # 创建所有表
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def disconnect(self):
        """断开数据库连接"""
        await self.engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:  # type: ignore
        """获取数据库会话"""
        async with self.session_factory() as session:
            yield session


# 创建全局数据库实例
db = Database()
