"""
Database Management Module
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import asyncpg

from .config import DatabaseConfig


class SlaveDatabase:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self._status = {"connected": False, "error": None}

    async def connect(self):
        """连接数据库"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
            )
            self._status = {"connected": True, "error": None}
            await self._init_tables()
        except Exception as e:
            self._status = {"connected": False, "error": str(e)}
            logging.error(f"Database connection error: {e}")
            raise

    async def disconnect(self):
        """断开数据库连接"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._status = {"connected": False, "error": None}

    @asynccontextmanager
    async def connection(self):
        """获取数据库连接"""
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self):
        """获取事务连接"""
        async with self.connection() as conn:
            async with conn.transaction():
                yield conn

    async def execute(self, query: str, *args) -> str:
        """执行SQL查询"""
        async with self.connection() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[Dict]:
        """执行查询并返回所有结果"""
        async with self.connection() as conn:
            records = await conn.fetch(query, *args)
            return [dict(record) for record in records]

    async def fetchrow(self, query: str, *args) -> Optional[Dict]:
        """执行查询并返回单行结果"""
        async with self.connection() as conn:
            record = await conn.fetchrow(query, *args)
            return dict(record) if record else None

    async def fetchval(self, query: str, *args) -> Any:
        """执行查询并返回单个值"""
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)

    async def _init_tables(self):
        """初始化数据库表"""
        async with self.transaction() as conn:
            # 创建设备表
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    config JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 创建用户表
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(50) PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    permissions JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 创建设置表
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key VARCHAR(100) PRIMARY KEY,
                    value JSONB NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 创建指标表
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    type VARCHAR(20) NOT NULL,
                    metrics JSONB NOT NULL
                )
            """
            )

            # 创建告警表
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    type VARCHAR(20) NOT NULL,
                    level VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP WITH TIME ZONE
                )
            """
            )

            # 创建同步历史表
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_history (
                    id SERIAL PRIMARY KEY,
                    sync_id VARCHAR(50) NOT NULL,
                    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    end_time TIMESTAMP WITH TIME ZONE,
                    status VARCHAR(20) NOT NULL,
                    config JSONB,
                    errors JSONB
                )
            """
            )

    async def store_metrics(self, metrics: Dict):
        """存储系统指标"""
        async with self.transaction() as conn:
            await conn.execute(
                """
                INSERT INTO metrics (type, metrics)
                VALUES ($1, $2)
            """,
                "system",
                metrics,
            )

    async def store_alert(self, alert: Dict):
        """存储告警信息"""
        async with self.transaction() as conn:
            await conn.execute(
                """
                INSERT INTO alerts (type, level, message)
                VALUES ($1, $2, $3)
            """,
                alert["type"],
                alert["level"],
                alert["message"],
            )

    async def store_sync_history(self, sync_data: Dict):
        """存储同步历史"""
        async with self.transaction() as conn:
            await conn.execute(
                """
                INSERT INTO sync_history (
                    sync_id, start_time, end_time,
                    status, config, errors
                )
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                sync_data["id"],
                sync_data["start_time"],
                sync_data["end_time"],
                sync_data["status"],
                sync_data["config"],
                sync_data["errors"],
            )

    async def get_status(self) -> Dict:
        """获取数据库状态"""
        if not self.pool:
            return self._status

        try:
            async with self.connection() as conn:
                # 检查连接
                await conn.execute("SELECT 1")
                # 获取数据库大小
                size = await conn.fetchval(
                    """
                    SELECT pg_database_size($1)
                """,
                    self.config.database,
                )
                # 获取表数量
                table_count = await conn.fetchval(
                    """
                    SELECT count(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """
                )

                return {
                    "connected": True,
                    "error": None,
                    "size_bytes": size,
                    "table_count": table_count,
                    "pool_size": self.pool.get_size(),
                    "pool_free": self.pool.get_free_size(),
                }
        except Exception as e:
            self._status = {"connected": False, "error": str(e)}
            return self._status
