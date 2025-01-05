"""查询优化器"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlalchemy.orm import selectinload, joinedload
from ncod.core.db.pool import DatabasePool
from ncod.core.logger import setup_logger

logger = setup_logger("query_optimizer")

T = TypeVar("T")


class QueryOptimizer:
    """查询优化器"""

    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self.query_cache: Dict[str, Any] = {}

    async def get_by_id(
        self,
        model: Type[T],
        id: str,
        session: AsyncSession,
        options: Optional[List] = None,
    ) -> Optional[T]:
        """通过ID获取记录"""
        try:
            query = select(model).where(model.id == id)
            if options:
                query = query.options(*options)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting {model.__name__} by id: {e}")
            raise

    async def get_all(
        self,
        model: Type[T],
        session: AsyncSession,
        options: Optional[List] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[T]:
        """获取所有记录"""
        try:
            query = select(model).offset(offset).limit(limit)
            if options:
                query = query.options(*options)
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting all {model.__name__}: {e}")
            raise

    def optimize_query(self, query: Select) -> Select:
        """优化查询"""
        try:
            # 这里可以添加查询优化逻辑
            # 例如：添加索引提示、优化JOIN顺序等
            return query
        except Exception as e:
            logger.error(f"Error optimizing query: {e}")
            return query

    def add_eager_loading(self, query: Select, relations: List[str]) -> Select:
        """添加预加载"""
        try:
            for relation in relations:
                if "." in relation:
                    # 处理嵌套关系
                    query = query.options(selectinload(relation))
                else:
                    # 处理直接关系
                    query = query.options(joinedload(relation))
            return query
        except Exception as e:
            logger.error(f"Error adding eager loading: {e}")
            return query

    async def execute_optimized(
        self, session: AsyncSession, query: Select, cache_key: Optional[str] = None
    ) -> Any:
        """执行优化后的查询"""
        try:
            # 检查缓存
            if cache_key and cache_key in self.query_cache:
                return self.query_cache[cache_key]

            # 优化查询
            optimized_query = self.optimize_query(query)

            # 执行查询
            result = await session.execute(optimized_query)

            # 缓存结果
            if cache_key:
                self.query_cache[cache_key] = result

            return result
        except Exception as e:
            logger.error(f"Error executing optimized query: {e}")
            raise
