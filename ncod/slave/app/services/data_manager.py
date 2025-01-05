"""
数据管理服务
负责数据存储策略、数据清理和归档
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from ..core.config import settings
from ..models.monitor import MonitorAlert, MonitorMetric

logger = logging.getLogger(__name__)


class DataManager:
    """数据管理服务"""

    def __init__(
        self,
        db: AsyncSession,
        retention_days: int = 30,  # 数据保留天数
        cleanup_interval: int = 86400,  # 清理间隔（秒）
        archive_interval: int = 7,  # 归档间隔（天）
        batch_size: int = 1000,  # 批处理大小
    ):
        """初始化数据管理服务

        Args:
            db: 数据库会话
            retention_days: 数据保留天数
            cleanup_interval: 清理间隔（秒）
            archive_interval: 归档间隔（天）
            batch_size: 批处理大小
        """
        self.db = db
        self.retention_days = retention_days
        self.cleanup_interval = cleanup_interval
        self.archive_interval = archive_interval
        self.batch_size = batch_size
        self._running = False
        self._task = None

    async def start(self):
        """启动数据管理服务"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._management_loop())
        logger.info("数据管理服务已启动")

    async def stop(self):
        """停止数据管理服务"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("数据管理服务已停止")

    async def _management_loop(self):
        """数据管理循环"""
        while self._running:
            try:
                # 执行数据清理
                await self.cleanup_old_data()

                # 执行数据归档
                await self.archive_data()

                # 执行数据优化
                await self.optimize_tables()

            except Exception as e:
                logger.error(f"数据管理任务失败: {str(e)}")

            await asyncio.sleep(self.cleanup_interval)

    async def cleanup_old_data(self):
        """清理过期数据"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)

            # 分批删除指标数据
            while True:
                delete_stmt = (
                    delete(MonitorMetric)
                    .where(MonitorMetric.timestamp < cutoff_date)
                    .limit(self.batch_size)
                )

                result = await self.db.execute(delete_stmt)
                deleted_count = result.rowcount
                await self.db.commit()

                logger.info(f"已删除 {deleted_count} 条过期指标数据")

                if deleted_count < self.batch_size:
                    break

            # 分批删除告警数据
            while True:
                delete_stmt = (
                    delete(MonitorAlert)
                    .where(MonitorAlert.timestamp < cutoff_date)
                    .limit(self.batch_size)
                )

                result = await self.db.execute(delete_stmt)
                deleted_count = result.rowcount
                await self.db.commit()

                logger.info(f"已删除 {deleted_count} 条过期告警数据")

                if deleted_count < self.batch_size:
                    break

        except Exception as e:
            logger.error(f"清理过期数据失败: {str(e)}")
            await self.db.rollback()

    async def archive_data(self):
        """归档历史数据"""
        try:
            archive_date = datetime.utcnow() - timedelta(days=self.archive_interval)

            # 聚合并归档指标数据
            metrics_query = (
                select(
                    MonitorMetric.metric_type,
                    func.date_trunc("hour", MonitorMetric.timestamp).label("hour"),
                    func.avg(MonitorMetric.value).label("avg_value"),
                    func.min(MonitorMetric.value).label("min_value"),
                    func.max(MonitorMetric.value).label("max_value"),
                    func.count().label("count"),
                )
                .where(MonitorMetric.timestamp < archive_date)
                .group_by(MonitorMetric.metric_type, text("hour"))
            )

            # 将聚合数据插入归档表
            archive_stmt = text(
                """
                INSERT INTO monitor_metric_archives 
                (metric_type, timestamp, avg_value, min_value, max_value, sample_count)
                VALUES (:metric_type, :hour, :avg_value, :min_value, :max_value, :count)
            """
            )

            result = await self.db.execute(metrics_query)
            archives = result.all()

            for archive in archives:
                await self.db.execute(
                    archive_stmt,
                    {
                        "metric_type": archive.metric_type,
                        "hour": archive.hour,
                        "avg_value": archive.avg_value,
                        "min_value": archive.min_value,
                        "max_value": archive.max_value,
                        "count": archive.count,
                    },
                )

            await self.db.commit()
            logger.info(f"已归档 {len(archives)} 条历史数据")

        except Exception as e:
            logger.error(f"归档历史数据失败: {str(e)}")
            await self.db.rollback()

    async def optimize_tables(self):
        """优化数据表"""
        try:
            # 执行表优化
            await self.db.execute(text("VACUUM ANALYZE monitor_metrics"))
            await self.db.execute(text("VACUUM ANALYZE monitor_alerts"))
            await self.db.execute(text("VACUUM ANALYZE monitor_metric_archives"))

            logger.info("数据表优化完成")

        except Exception as e:
            logger.error(f"数据表优化失败: {str(e)}")

    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            # 获取各表的记录数和大小
            stats = {}

            for table in [
                "monitor_metrics",
                "monitor_alerts",
                "monitor_metric_archives",
            ]:
                count_query = select(func.count()).select_from(text(table))
                size_query = text(f"SELECT pg_total_relation_size('{table}')")

                count_result = await self.db.execute(count_query)
                size_result = await self.db.execute(size_query)

                stats[table] = {
                    "record_count": count_result.scalar(),
                    "size_bytes": size_result.scalar(),
                }

            return {
                "tables": stats,
                "retention_days": self.retention_days,
                "archive_interval": self.archive_interval,
                "last_cleanup": (
                    self._last_cleanup.isoformat()
                    if hasattr(self, "_last_cleanup")
                    else None
                ),
                "last_archive": (
                    self._last_archive.isoformat()
                    if hasattr(self, "_last_archive")
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"获取存储统计信息失败: {str(e)}")
            return {}
