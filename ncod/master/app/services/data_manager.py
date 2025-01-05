"""
数据管理服务
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.monitor import MonitorAlert, MonitorMetric

# 配置日志
logger = logging.getLogger(__name__)


class DataManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def cleanup_old_data(self) -> Dict[str, int]:
        """清理旧数据"""
        try:
            # 计算保留时间
            retention_date = datetime.utcnow() - timedelta(
                days=settings.DATA_RETENTION_DAYS
            )

            # 删除旧的监控指标
            metrics_result = await self.db.execute(
                select(func.count())
                .select_from(MonitorMetric)
                .where(MonitorMetric.timestamp < retention_date)
            )
            metrics_count = metrics_result.scalar_one()

            if metrics_count > 0:
                await self.db.execute(
                    text(
                        "DELETE FROM monitor_metrics WHERE timestamp < :retention_date"
                    ),
                    {"retention_date": retention_date},
                )

            # 删除已解决的旧告警
            alerts_result = await self.db.execute(
                select(func.count())
                .select_from(MonitorAlert)
                .where(
                    and_(
                        MonitorAlert.resolved_at.isnot(None),
                        MonitorAlert.resolved_at < retention_date,
                    )
                )
            )
            alerts_count = alerts_result.scalar_one()

            if alerts_count > 0:
                await self.db.execute(
                    text(
                        "DELETE FROM monitor_alerts WHERE resolved_at IS NOT NULL AND \
                             resolved_at < :retention_date"
                    ),
                    {"retention_date": retention_date},
                )

            await self.db.commit()

            return {"deleted_metrics": metrics_count, "deleted_alerts": alerts_count}

        except Exception as e:
            logger.error(f"清理旧数据失败: {str(e)}")
            await self.db.rollback()
            raise

    async def archive_data(self, archive_before: datetime) -> Dict[str, int]:
        """归档数据"""
        try:
            # 获取需要归档的指标数据
            metrics_result = await self.db.execute(
                select(
                    MonitorMetric.metric_type,
                    func.min(MonitorMetric.value).label("min_value"),
                    func.max(MonitorMetric.value).label("max_value"),
                    func.avg(MonitorMetric.value).label("avg_value"),
                    func.count().label("sample_count"),
                )
                .where(MonitorMetric.timestamp < archive_before)
                .group_by(MonitorMetric.metric_type)
            )
            metrics = metrics_result.all()

            # 创建归档记录
            for metric in metrics:
                archive = MetricArchive(
                    metric_type=metric.metric_type,
                    start_time=archive_before - timedelta(days=1),
                    end_time=archive_before,
                    min_value=metric.min_value,
                    max_value=metric.max_value,
                    avg_value=metric.avg_value,
                    sample_count=metric.sample_count,
                )
                self.db.add(archive)

            # 删除已归档的数据
            await self.db.execute(
                text("DELETE FROM monitor_metrics WHERE timestamp < :archive_before"),
                {"archive_before": archive_before},
            )

            await self.db.commit()

            return {"archived_metrics": sum(m.sample_count for m in metrics)}

        except Exception as e:
            logger.error(f"归档数据失败: {str(e)}")
            await self.db.rollback()
            raise

    async def optimize_tables(self) -> None:
        """优化数据表"""
        try:
            # 对主要表执行VACUUM ANALYZE
            tables = ["monitor_metrics", "monitor_alerts", "metric_archives"]

            for table in tables:
                await self.db.execute(text(f"VACUUM ANALYZE {table}"))

            await self.db.commit()

        except Exception as e:
            logger.error(f"优化数据表失败: {str(e)}")
            await self.db.rollback()
            raise

    async def get_storage_stats(self) -> Dict[str, Dict[str, int]]:
        """获取存储统计信息"""
        try:
            stats = {}

            # 获取监控指标统计
            metrics_result = await self.db.execute(
                select(
                    func.count().label("total_records"),
                    func.pg_total_relation_size("monitor_metrics").label("total_size"),
                ).select_from(MonitorMetric)
            )
            metrics_stats = metrics_result.first()

            stats["monitor_metrics"] = {
                "total_records": metrics_stats.total_records,
                "total_size_bytes": metrics_stats.total_size,
            }

            # 获取告警统计
            alerts_result = await self.db.execute(
                select(
                    func.count().label("total_records"),
                    func.pg_total_relation_size("monitor_alerts").label("total_size"),
                ).select_from(MonitorAlert)
            )
            alerts_stats = alerts_result.first()

            stats["monitor_alerts"] = {
                "total_records": alerts_stats.total_records,
                "total_size_bytes": alerts_stats.total_size,
            }

            # 获取归档统计
            archives_result = await self.db.execute(
                select(
                    func.count().label("total_records"),
                    func.pg_total_relation_size("metric_archives").label("total_size"),
                ).select_from(MetricArchive)
            )
            archives_stats = archives_result.first()

            stats["metric_archives"] = {
                "total_records": archives_stats.total_records,
                "total_size_bytes": archives_stats.total_size,
            }

            return stats

        except Exception as e:
            logger.error(f"获取存储统计信息失败: {str(e)}")
            raise
