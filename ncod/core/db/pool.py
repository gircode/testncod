"""数据库连接池管理器"""

import logging
from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from ncod.core.config import config
from ncod.core.logger import setup_logger

logger = setup_logger("db_pool")


class DatabasePool:
    """数据库连接池管理器"""

    def __init__(self):
        self.write_engine: Optional[AsyncEngine] = None
        self.read_engines: List[AsyncEngine] = []
        self.current_read_index: int = 0
        self.session_factory: Optional[async_sessionmaker] = None

    async def init_pool(self):
        """初始化连接池"""
        try:
            # 创建写入引擎
            self.write_engine = create_async_engine(
                config.database_write_url,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=config.db_pool_size,
                max_overflow=config.db_max_overflow,
                pool_timeout=config.db_pool_timeout,
                pool_recycle=config.db_pool_recycle,
                pool_pre_ping=True,
                echo=config.db_echo,
            )

            # 创建读取引擎
            for url in config.database_read_urls:
                engine = create_async_engine(
                    url,
                    poolclass=AsyncAdaptedQueuePool,
                    pool_size=config.db_pool_size,
                    max_overflow=config.db_max_overflow,
                    pool_timeout=config.db_pool_timeout,
                    pool_recycle=config.db_pool_recycle,
                    pool_pre_ping=True,
                    echo=config.db_echo,
                )
                self.read_engines.append(engine)

            # 创建会话工厂
            self.session_factory = async_sessionmaker(
                bind=self.write_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )

            logger.info(
                f"Database pool initialized with {len(self.read_engines)} read replicas"
            )
        except Exception as e:
            logger.error(f"Error initializing database pool: {e}")
            raise

    async def close_pool(self):
        """关闭连接池"""
        try:
            if self.write_engine:
                await self.write_engine.dispose()

            for engine in self.read_engines:
                await engine.dispose()

            logger.info("Database pool closed")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")
            raise

    def get_read_session(self) -> AsyncSession:
        """获取读取会话(轮询负载均衡)"""
        try:
            if not self.read_engines:
                return self.get_write_session()

            # 轮询选择读取引擎
            engine = self.read_engines[self.current_read_index]
            self.current_read_index = (self.current_read_index + 1) % len(
                self.read_engines
            )

            return AsyncSession(engine, expire_on_commit=False, autoflush=False)
        except Exception as e:
            logger.error(f"Error getting read session: {e}")
            return self.get_write_session()

    def get_write_session(self) -> AsyncSession:
        """获取写入会话"""
        try:
            if not self.session_factory:
                raise RuntimeError("Database pool not initialized")
            return self.session_factory()
        except Exception as e:
            logger.error(f"Error getting write session: {e}")
            raise

    async def get_pool_status(self) -> Dict:
        """获取连接池状态"""
        try:
            write_pool = self.write_engine.pool
            status = {
                "write_pool": {
                    "size": write_pool.size(),
                    "checked_in": write_pool.checkedin(),
                    "checked_out": write_pool.checkedout(),
                    "overflow": write_pool.overflow(),
                },
                "read_pools": [],
            }

            for i, engine in enumerate(self.read_engines):
                pool = engine.pool
                status["read_pools"].append(
                    {
                        "index": i,
                        "size": pool.size(),
                        "checked_in": pool.checkedin(),
                        "checked_out": pool.checkedout(),
                        "overflow": pool.overflow(),
                    }
                )

            return status
        except Exception as e:
            logger.error(f"Error getting pool status: {e}")
            return {}


# 创建全局连接池实例
db_pool = DatabasePool()
