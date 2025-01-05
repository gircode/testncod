"""
Database Module
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

import asyncpg

from ..config.dev import DATABASE_CONFIG


class DatabaseManager:
    """数据库连接管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

    async def init_pool(self) -> None:
        """初始化连接池"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                min_size=self.config.get("min_connections", 1),
                max_size=self.config.get("max_connections", 10),
            )

    async def close_pool(self) -> None:
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            self.pool = None

    @asynccontextmanager
    async def connection(self):
        """获取数据库连接的上下文管理器"""
        if not self.pool:
            await self.init_pool()

        async with self.pool.acquire() as conn:
            try:
                yield conn
            except Exception as e:
                await conn.execute("ROLLBACK")
                raise e

    async def execute(self, query: str, *args) -> str:
        """执行SQL查询"""
        async with self.connection() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list:
        """执行查询并返回所有结果"""
        async with self.connection() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """执行查询并返回单行结果"""
        async with self.connection() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """执行查询并返回单个值"""
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)
