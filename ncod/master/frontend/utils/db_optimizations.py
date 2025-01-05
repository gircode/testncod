"""Db Optimizations模块"""

import json
import logging
import time
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union

import redis
from database import db_manager
from sqlalchemy import text
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

# Redis连接
try:
    redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None


def cache_key(prefix: str, *args, **kwargs) -> str:
    """生成缓存键"""
    key_parts = [prefix]
    if args:
        key_parts.extend([str(arg) for arg in args])
    if kwargs:
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    return ":".join(key_parts)


def redis_cache(prefix: str, expire: int = 300):
    """Redis缓存装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not redis_client:
                return await func(*args, **kwargs)

            key = cache_key(prefix, *args, **kwargs)

            # 尝试从缓存获取
            cached = redis_client.get(key)
            if cached:
                try:
                    return json.loads(cached)
                except Exception:
                    pass

            # 执行函数
            result = await func(*args, **kwargs)

            # 缓存结果
            try:
                redis_client.setex(key, expire, json.dumps(result))
            except Exception as e:
                logger.error(f"Failed to cache result: {e}")

            return result

        return wrapper

    return decorator


def clear_cache(prefix: str):
    """清除指定前缀的缓存"""
    if not redis_client:
        return

    try:
        keys = redis_client.keys(f"{prefix}:*")
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")


class QueryOptimizer:
    """查询优化器"""

    @staticmethod
    def paginate(query, page: int = 1, per_page: int = 20) -> Tuple[List[Any], int]:
        """分页查询"""
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def eager_load(query, *relationships):
        """预加载关联数据"""
        for relationship in relationships:
            query = query.options(joinedload(relationship))
        return query

    @staticmethod
    def bulk_load(query, relationship):
        """批量加载关联数据"""
        return query.options(selectinload(relationship))

    @staticmethod
    def with_count(session, table, *conditions):
        """带计数的查询"""
        return session.query(table, func.count().over().label("total_count")).filter(
            *conditions
        )

    @staticmethod
    def chunked_query(query, chunk_size: int = 1000):
        """分块查询"""
        offset = 0
        while True:
            chunk = query.offset(offset).limit(chunk_size).all()
            if not chunk:
                break
            yield chunk
            offset += chunk_size

    @staticmethod
    def analyze_query(session, query):
        """分析查询性能"""
        try:
            start_time = time.time()
            explain = session.execute(
                text(
                    f"EXPLAIN ANALYZE \
                         {str(query.statement.compile(compile_kwargs={'literal_binds': True}))}"
                )
            ).fetchall()
            duration = time.time() - start_time

            return {"duration": duration, "explain": [row[0] for row in explain]}
        except Exception as e:
            logger.error(f"Failed to analyze query: {e}")
            return None


class AsyncQueryOptimizer:
    """异步查询优化器"""

    @staticmethod
    async def paginate(
        query, page: int = 1, per_page: int = 20
    ) -> Tuple[List[Any], int]:
        """异步分页查询"""
        total = await query.count()
        items = await query.offset((page - 1) * per_page).limit(per_page).gino.all()
        return items, total

    @staticmethod
    async def eager_load(query, *relationships):
        """异步预加载关联数据"""
        for relationship in relationships:
            query = query.load(relationship)
        return await query.gino.all()

    @staticmethod
    async def chunked_query(query, chunk_size: int = 1000):
        """异步分块查询"""
        offset = 0
        while True:
            chunk = await query.offset(offset).limit(chunk_size).gino.all()
            if not chunk:
                break
            yield chunk
            offset += chunk_size


def optimize_query(query, options: Dict):
    """优化查询"""
    optimizer = QueryOptimizer()

    # 应用分页
    if "page" in options and "per_page" in options:
        return optimizer.paginate(
            query, page=options["page"], per_page=options["per_page"]
        )

    # 预加载关联数据
    if "eager_load" in options:
        query = optimizer.eager_load(query, *options["eager_load"])

    # 批量加载关联数据
    if "bulk_load" in options:
        query = optimizer.bulk_load(query, options["bulk_load"])

    # 分块查询
    if "chunk_size" in options:
        return optimizer.chunked_query(query, options["chunk_size"])

    return query.all()


def analyze_slow_queries(session, threshold: float = 1.0):
    """分析慢查询"""
    try:
        result = session.execute(
            text(
                """
            SELECT query, calls, total_time, mean_time, rows
            FROM pg_stat_statements
            WHERE mean_time > :threshold
            ORDER BY mean_time DESC
            LIMIT 10
        """
            ),
            {"threshold": threshold * 1000},
        )  # 转换为毫秒

        return [
            {
                "query": row[0],
                "calls": row[1],
                "total_time": row[2],
                "mean_time": row[3],
                "rows": row[4],
            }
            for row in result
        ]
    except Exception as e:
        logger.error(f"Failed to analyze slow queries: {e}")
        return []


def create_indexes(session, model, columns: List[str]):
    """创建索引"""
    try:
        table_name = model.__tablename__
        for column in columns:
            index_name = f"ix_{table_name}_{column}"
            session.execute(
                text(
                    f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name} ({column})
            """
                )
            )
        session.commit()
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        session.rollback()


def analyze_table_stats(session, table_name: str) -> Dict:
    """分析表统计信息"""
    try:
        result = session.execute(
            text(
                f"""
            SELECT
                reltuples::bigint AS row_count,
                pg_size_pretty(pg_total_relation_size('{table_name}')) AS total_size,
                pg_size_pretty(pg_table_size('{table_name}')) AS table_size,
                pg_size_pretty(pg_indexes_size('{table_name}')) AS index_size,
                n_live_tup AS live_rows,
                n_dead_tup AS dead_rows,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            JOIN pg_class ON pg_class.relname = pg_stat_user_tables.relname
            WHERE pg_stat_user_tables.relname = :table_name
        """
            ),
            {"table_name": table_name},
        ).fetchone()

        if result:
            return {
                "row_count": result[0],
                "total_size": result[1],
                "table_size": result[2],
                "index_size": result[3],
                "live_rows": result[4],
                "dead_rows": result[5],
                "last_vacuum": result[6],
                "last_autovacuum": result[7],
                "last_analyze": result[8],
                "last_autoanalyze": result[9],
            }
        return {}
    except Exception as e:
        logger.error(f"Failed to analyze table stats: {e}")
        return {}
