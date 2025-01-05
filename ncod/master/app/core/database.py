"""
数据库优化模块
"""

import functools
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

import backoff
from app.core.config import settings
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool, Pool

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """基础模型类"""


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    @backoff.on_exception(
        backoff.expo, (OperationalError, SQLAlchemyError), max_tries=5, max_time=30
    )
    def setup(self):
        """初始化数据库连接"""
        if not self.engine:
            if not settings.SQLALCHEMY_DATABASE_URI:
                raise ValueError("Database URI is not configured")

            self.engine = create_async_engine(
                str(settings.SQLALCHEMY_DATABASE_URI),
                echo=False,
                pool_pre_ping=True,  # 添加连接健康检查
                pool_size=settings.SQLALCHEMY_POOL_SIZE,
                max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
                pool_timeout=settings.SQLALCHEMY_POOL_TIMEOUT,
                pool_recycle=settings.SQLALCHEMY_POOL_RECYCLE,
                poolclass=AsyncAdaptedQueuePool,
                connect_args={
                    "server_settings": {
                        "application_name": "ncod_master",
                        "statement_timeout": "60000",  # 60秒查询超时
                        "idle_in_transaction_session_timeout": "300000",  # 5分钟事务超时
                    }
                },
            )

            self.session_factory = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        if not self.session_factory:
            self.setup()

        if not self.session_factory:
            raise RuntimeError("Database session factory is not initialized")

        session: AsyncSession = self.session_factory()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """获取事务会话"""
        async with self.session() as session:
            async with session.begin():
                try:
                    yield session
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Transaction error: {str(e)}")
                    raise


class QueryOptimizer:
    """查询优化器"""

    @staticmethod
    def optimize_query(query):
        """优化查询"""
        # 这里可以添加查询优化逻辑
        # 例如：添加必要的 JOIN、索引提示等
        return query

    @staticmethod
    def paginate(query, page: int = 1, per_page: int = 20, count: bool = True):
        """分页查询"""
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 20

        items = query.limit(per_page).offset((page - 1) * per_page)

        if count:
            total = query.count()
            pages = (total + per_page - 1) // per_page
            has_next = page < pages
            has_prev = page > 1

            return {
                "items": items,
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }

        return {"items": items, "page": page, "per_page": per_page}


class BulkOperationManager:
    """批量操作管理器"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.items: List[Any] = []
        self.batch_size = 1000

    async def add(self, item: Any):
        """添加项目"""
        self.items.append(item)

        if len(self.items) >= self.batch_size:
            await self.flush()

    async def flush(self):
        """刷新批量操作"""
        if not self.items:
            return

        await self.session.execute(
            text("INSERT INTO items VALUES :items"), {"items": self.items}
        )
        await self.session.flush()
        self.items = []

    async def commit(self):
        """提交批量操作"""
        await self.flush()
        await self.session.commit()


class ConnectionManager:
    """连接管理器"""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.pool_stats: Dict[str, int] = {}

    async def get_pool_status(self) -> Dict[str, int]:
        """获取连接池状态"""
        pool = self.engine.pool
        if isinstance(pool, Pool):
            return {
                "size": pool._size,  # type: ignore
                "checked_in": pool._checkedin,  # type: ignore
                "checked_out": pool._checkedout,  # type: ignore
                "overflow": pool._overflow,  # type: ignore
            }
        return {"size": 0, "checked_in": 0, "checked_out": 0, "overflow": 0}

    async def check_connection(self) -> bool:
        """检查数据库连接"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def reset_pool(self):
        """重置连接池"""
        await self.engine.dispose()


class IndexManager:
    """索引管理器"""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def analyze_table(self, table_name: str) -> Dict[str, Any]:
        """分析表统计信息"""
        async with self.engine.connect() as conn:
            # 获取表的行数
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            total_rows = result.scalar()

            # 获取表的大小
            result = await conn.execute(
                text(
                    f"""
                SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))
            """
                )
            )
            table_size = result.scalar()

            # 获取索引信息
            result = await conn.execute(
                text(
                    f"""
                SELECT
                    indexname,
                    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
                FROM pg_indexes
                WHERE tablename = '{table_name}'
            """
                )
            )
            indexes = [dict(row) for row in result]

            return {
                "table_name": table_name,
                "total_rows": total_rows,
                "table_size": table_size,
                "indexes": indexes,
            }

    async def suggest_indexes(self, table_name: str) -> List[str]:
        """建议创建的索引"""
        async with self.engine.connect() as conn:
            # 获取查询模式
            result = await conn.execute(
                text(
                    f"""
                SELECT
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    null_frac
                FROM pg_stats
                WHERE tablename = '{table_name}'
                ORDER BY n_distinct DESC
            """
                )
            )
            columns = [dict(row) for row in result]

            # 分析并建议索引
            suggestions = []
            for col in columns:
                if col["n_distinct"] > 100 and col["null_frac"] < 0.5:
                    suggestions.append(
                        f"CREATE INDEX idx_{table_name}_{col['attname']} "
                        f"ON {table_name} ({col['attname']})"
                    )

            return suggestions


class QueryProfiler:
    """查询分析器"""

    def __init__(self):
        self.queries: List[Dict[str, Any]] = []

    def record_query(self, query: str, params: Dict[str, Any], duration: float):
        """记录查询"""
        self.queries.append(
            {
                "query": query,
                "params": params,
                "duration": duration,
                "timestamp": time.time(),
            }
        )

    def get_slow_queries(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """获取慢查询"""
        return [q for q in self.queries if q["duration"] >= threshold]

    def clear(self):
        """清空记录"""
        self.queries = []


def db_profiler(threshold: float = 1.0):
    """数据库性能分析装饰器"""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if duration >= threshold:
                    print(
                        f"Slow query detected: {func.__name__} "
                        f"took {duration:.2f} seconds"
                    )

        return wrapper

    return decorator
