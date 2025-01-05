"""Query Optimization模块"""

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import and_, asc, desc, func, or_, text
from sqlalchemy.orm import contains_eager, joinedload, selectinload
from sqlalchemy.sql import Select

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """查询优化器"""

    def __init__(self, session):
        self.session = session
        self.query_stats = defaultdict(list)

    @classmethod
    def log_query_time(cls, func):
        """记录查询执行时间的装饰器"""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            # 记录查询统计信息
            func_name = func.__name__
            self.query_stats[func_name].append(
                {
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # 只保留最近的100条记录
            if len(self.query_stats[func_name]) > 100:
                self.query_stats[func_name] = self.query_stats[func_name][-100:]

            logger.debug(f"{func_name} execution time: {execution_time:.4f}s")
            return result

        return wrapper

    def get_query_stats(self) -> Dict[str, Dict[str, float]]:
        """获取查询统计信息"""
        stats = {}
        for query_name, times in self.query_stats.items():
            if times:
                stats[query_name] = {
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "count": len(times),
                }
        return stats

    def optimize_query(self, query: Select) -> Select:
        """优化查询"""
        # 这里可以添加通用的查询优化逻辑
        return query

    @log_query_time
    def paginated_query(
        self,
        query: Select,
        page: int = 1,
        per_page: int = 20,
        order_by: Optional[str] = None,
        order_direction: str = "asc",
    ) -> Tuple[List[Any], int]:
        """分页查询"""
        # 获取总数
        total = self.session.query(func.count()).select_from(query.subquery()).scalar()

        # 添加排序
        if order_by:
            direction = asc if order_direction == "asc" else desc
            query = query.order_by(direction(order_by))

        # 添加分页
        query = query.offset((page - 1) * per_page).limit(per_page)

        # 执行查询
        results = self.session.execute(query).scalars().all()

        return results, total

    @log_query_time
    def bulk_insert(self, model, data: List[Dict]) -> bool:
        """批量插入"""
        try:
            self.session.bulk_insert_mappings(model, data)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            self.session.rollback()
            return False

    @log_query_time
    def bulk_update(self, model, data: List[Dict], key_field: str = "id") -> bool:
        """批量更新"""
        try:
            self.session.bulk_update_mappings(model, data)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Bulk update failed: {e}")
            self.session.rollback()
            return False

    def eager_load(self, query: Select, relations: List[str]) -> Select:
        """添加预加载"""
        for relation in relations:
            query = query.options(joinedload(relation))
        return query

    def apply_filters(self, query: Select, filters: Dict[str, Any], model) -> Select:
        """应用过滤条件"""
        for field, value in filters.items():
            if hasattr(model, field):
                if isinstance(value, (list, tuple)):
                    query = query.filter(getattr(model, field).in_(value))
                else:
                    query = query.filter(getattr(model, field) == value)
        return query

    def search_query(
        self, query: Select, search_text: str, search_fields: List[str], model
    ) -> Select:
        """添加搜索条件"""
        if search_text and search_fields:
            conditions = []
            for field in search_fields:
                if hasattr(model, field):
                    conditions.append(getattr(model, field).ilike(f"%{search_text}%"))
            if conditions:
                query = query.filter(or_(*conditions))
        return query

    def date_range_filter(
        self,
        query: Select,
        model,
        date_field: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Select:
        """添加日期范围过滤"""
        if hasattr(model, date_field):
            if start_date:
                query = query.filter(getattr(model, date_field) >= start_date)
            if end_date:
                query = query.filter(getattr(model, date_field) <= end_date)
        return query

    @log_query_time
    def get_aggregated_data(
        self,
        query: Select,
        group_by: Union[str, List[str]],
        aggregations: Dict[str, str],
        model,
    ) -> List[Dict]:
        """获取聚合数据"""
        try:
            # 处理分组字段
            if isinstance(group_by, str):
                group_by = [group_by]

            group_columns = [getattr(model, field) for field in group_by]

            # 处理聚合函数
            agg_columns = []
            for field, agg_func in aggregations.items():
                if hasattr(model, field):
                    column = getattr(model, field)
                    if agg_func == "count":
                        agg_columns.append(func.count(column).label(f"{field}_count"))
                    elif agg_func == "sum":
                        agg_columns.append(func.sum(column).label(f"{field}_sum"))
                    elif agg_func == "avg":
                        agg_columns.append(func.avg(column).label(f"{field}_avg"))
                    elif agg_func == "min":
                        agg_columns.append(func.min(column).label(f"{field}_min"))
                    elif agg_func == "max":
                        agg_columns.append(func.max(column).label(f"{field}_max"))

            # 构建查询
            query = self.session.query(*group_columns, *agg_columns)
            query = query.group_by(*group_columns)

            # 执行查询
            results = query.all()

            # 转换结果为字典列表
            return [
                {
                    **{field: getattr(row, field) for field in group_by},
                    **{
                        f"{field}_{agg_func}": getattr(row, f"{field}_{agg_func}")
                        for field, agg_func in aggregations.items()
                    },
                }
                for row in results
            ]

        except Exception as e:
            logger.error(f"Aggregation query failed: {e}")
            return []

    def create_materialized_view(
        self,
        view_name: str,
        query: Select,
        refresh_interval: int = 3600,  # 默认1小时刷新一次
    ):
        """创建物化视图"""
        try:
            # 创建物化视图
            create_view_sql = f"""
            CREATE MATERIALIZED VIEW IF NOT EXISTS {view_name} AS
            {query}
            WITH DATA;
            """
            self.session.execute(text(create_view_sql))

            # 创建刷新函数
            refresh_function_sql = f"""
            CREATE OR REPLACE FUNCTION refresh_{view_name}()
            RETURNS void AS $$
            BEGIN
                REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name};
            END;
            $$ LANGUAGE plpgsql;
            """
            self.session.execute(text(refresh_function_sql))

            # 创建定时任务
            schedule_refresh_sql = f"""
            SELECT cron.schedule(
                'refresh_{view_name}',
                '{refresh_interval} seconds',
                'SELECT refresh_{view_name}()'
            );
            """
            self.session.execute(text(schedule_refresh_sql))

            self.session.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to create materialized view: {e}")
            self.session.rollback()
            return False

    def create_index(
        self,
        table_name: str,
        column_names: List[str],
        index_name: Optional[str] = None,
        unique: bool = False,
        partial: Optional[str] = None,
    ):
        """创建索引"""
        try:
            # 生成索引名称
            if not index_name:
                index_name = f"idx_{table_name}_{'_'.join(column_names)}"

            # 构建SQL
            create_index_sql = f"""
            CREATE {' UNIQUE' if unique else ''} INDEX IF NOT EXISTS {index_name}
            ON {table_name} ({','.join(column_names)})
            {f'WHERE {partial}' if partial else ''};
            """

            self.session.execute(text(create_index_sql))
            self.session.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            self.session.rollback()
            return False

    def analyze_query(self, query: Select) -> Dict[str, Any]:
        """分析查询性能"""
        try:
            # 执行EXPLAIN ANALYZE
            explain_sql = f"EXPLAIN (ANALYZE, FORMAT JSON) {query}"
            result = self.session.execute(text(explain_sql)).scalar()

            # 解析结果
            plan = json.loads(result)[0]

            # 提取关键信息
            analysis = {
                "execution_time": plan["Execution Time"],
                "planning_time": plan["Planning Time"],
                "total_cost": plan["Plan"]["Total Cost"],
                "actual_rows": plan["Plan"]["Actual Rows"],
                "actual_loops": plan["Plan"]["Actual Loops"],
            }

            return analysis

        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {}


class QueryCache:
    """查询缓存"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 300  # 默认缓存5分钟

    def get_cache_key(self, query: Select) -> str:
        """生成缓存键"""
        return f"query_cache:{hash(str(query))}"

    def get_cached_result(self, query: Select) -> Optional[List[Dict]]:
        """获取缓存的查询结果"""
        try:
            cache_key = self.get_cache_key(query)
            cached_data = self.redis.get(cache_key)

            if cached_data:
                return json.loads(cached_data)

            return None

        except Exception as e:
            logger.error(f"Failed to get cached result: {e}")
            return None

    def cache_result(
        self, query: Select, result: List[Dict], ttl: Optional[int] = None
    ):
        """缓存查询结果"""
        try:
            cache_key = self.get_cache_key(query)
            self.redis.setex(cache_key, ttl or self.default_ttl, json.dumps(result))
            return True

        except Exception as e:
            logger.error(f"Failed to cache result: {e}")
            return False

    def invalidate_cache(self, query: Select):
        """使缓存失效"""
        try:
            cache_key = self.get_cache_key(query)
            self.redis.delete(cache_key)
            return True

        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return False
