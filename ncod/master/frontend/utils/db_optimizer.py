"""数据库优化工具"""

import logging
from typing import Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from ...core.config import settings

logger = logging.getLogger(__name__)


class DBOptimizer:
    """数据库优化器"""

    def __init__(self, engine: Optional[Engine] = None):
        """初始化数据库优化器

        Args:
            engine: SQLAlchemy引擎实例,如果为None则使用配置中的默认连接
        """
        self.engine = engine or create_engine(settings.SQLALCHEMY_DATABASE_URI)

    def analyze_table_stats(self, table_name: str) -> Dict:
        """分析表统计信息

        Args:
            table_name: 表名

        Returns:
            表统计信息字典
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"ANALYZE {table_name}"))
                stats = conn.execute(
                    text(
                        f"""
                    SELECT 
                        reltuples::bigint AS row_count,
                        pg_size_pretty(pg_total_relation_size('{table_name}')) AS total_size,
                        pg_size_pretty(pg_table_size('{table_name}')) AS table_size,
                        pg_size_pretty(pg_indexes_size('{table_name}')) AS index_size
                    FROM pg_class 
                    WHERE relname = '{table_name}'
                    """
                    )
                ).first()

                return {
                    "row_count": stats.row_count,
                    "total_size": stats.total_size,
                    "table_size": stats.table_size,
                    "index_size": stats.index_size,
                }

        except SQLAlchemyError as e:
            logger.error(f"分析表统计信息失败: {str(e)}")
            return {}

    def get_slow_queries(self, min_duration: float = 1.0) -> List[Dict]:
        """获取慢查询列表

        Args:
            min_duration: 最小执行时间(秒)

        Returns:
            慢查询列表
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(
                        f"""
                    SELECT 
                        query,
                        calls,
                        total_time / 1000 as total_seconds,
                        mean_time / 1000 as mean_seconds,
                        rows
                    FROM pg_stat_statements
                    WHERE mean_time / 1000 > {min_duration}
                    ORDER BY mean_time DESC
                    LIMIT 10
                    """
                    )
                )

                return [dict(row) for row in result]

        except SQLAlchemyError as e:
            logger.error(f"获取慢查询失败: {str(e)}")
            return []

    def vacuum_analyze(self, table_name: str) -> bool:
        """执行VACUUM ANALYZE

        Args:
            table_name: 表名

        Returns:
            是否成功
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"VACUUM ANALYZE {table_name}"))
                return True

        except SQLAlchemyError as e:
            logger.error(f"执行VACUUM ANALYZE失败: {str(e)}")
            return False


db_optimizer = DBOptimizer()
