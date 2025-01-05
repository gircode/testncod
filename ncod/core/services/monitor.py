"""监控服务"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ...models.monitor import SystemMetric
from ...utils.logger import logger


class MonitorService:
    def save_system_metrics(self, db: Session, metrics: Dict[str, Any]) -> None:
        """保存系统指标"""
        try:
            metric = SystemMetric(
                cpu_percent=metrics["cpu_percent"],
                memory_percent=metrics["memory_percent"],
                disk_usage=metrics["disk_usage"],
                disk_free=metrics["disk_free"],
                network_sent=metrics["network_io"]["bytes_sent"],
                network_recv=metrics["network_io"]["bytes_recv"],
                connections=metrics["connections"],
                timestamp=datetime.fromisoformat(metrics["timestamp"]),
            )
            db.add(metric)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("保存系统指标失败", exc_info=True)
            raise

    def get_metrics_history(
        self, db: Session, start_time: datetime, end_time: datetime = None
    ) -> List[SystemMetric]:
        """获取历史指标"""
        try:
            if end_time is None:
                end_time = datetime.utcnow()

            return (
                db.query(SystemMetric)
                .filter(SystemMetric.timestamp.between(start_time, end_time))
                .order_by(SystemMetric.timestamp.desc())
                .all()
            )
        except Exception as e:
            logger.error("获取历史指标失败", exc_info=True)
            raise
