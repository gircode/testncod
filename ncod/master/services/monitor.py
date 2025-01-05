"""设备监控服务"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func
from ncod.core.logger import setup_logger
from ncod.core.db.transaction import transaction_manager
from ncod.master.models.monitor import DeviceMetric, DeviceAlert, Monitor
from ncod.core.cache.manager import cache_manager
from ncod.master.database import get_session

logger = setup_logger("monitor_service")


class MonitorService:
    """监控服务"""

    def __init__(self):
        self.transaction = transaction_manager
        self.cache = cache_manager
        self.metric_cache_ttl = 300  # 5分钟

    async def record_device_metrics(self, device_id: str, metrics: Dict) -> bool:
        """记录设备指标"""
        try:
            async with self.transaction.transaction() as session:
                # 创建指标记录
                for metric_type, value in metrics.items():
                    metric = DeviceMetric(
                        device_id=device_id,
                        metric_type=metric_type,
                        value=value.get("value"),
                        unit=value.get("unit", ""),
                        collected_at=datetime.utcnow(),
                    )
                    session.add(metric)

                # 更新缓存
                cache_key = f"device_metrics:{device_id}"
                await self.cache.set(cache_key, metrics, self.metric_cache_ttl)

                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error recording device metrics: {e}")
            return False

    async def get_device_metrics(
        self,
        device_id: str,
        metric_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict]:
        """获取设备指标"""
        try:
            # 尝试从缓存获取最新指标
            if not start_time and not end_time:
                cache_key = f"device_metrics:{device_id}"
                cached = await self.cache.get(cache_key)
                if cached:
                    return cached

            async with self.transaction.transaction() as session:
                stmt = select(DeviceMetric).where(DeviceMetric.device_id == device_id)

                if metric_type:
                    stmt = stmt.where(DeviceMetric.metric_type == metric_type)
                if start_time:
                    stmt = stmt.where(DeviceMetric.collected_at >= start_time)
                if end_time:
                    stmt = stmt.where(DeviceMetric.collected_at <= end_time)

                stmt = stmt.order_by(DeviceMetric.collected_at.desc())
                result = await session.execute(stmt)
                metrics = result.scalars().all()

                return [metric.to_dict() for metric in metrics]
        except Exception as e:
            logger.error(f"Error getting device metrics: {e}")
            return []

    async def create_alert(
        self, device_id: str, alert_type: str, level: str, message: str
    ) -> bool:
        """创建设备告警"""
        try:
            async with self.transaction.transaction() as session:
                alert = DeviceAlert(
                    device_id=device_id,
                    alert_type=alert_type,
                    level=level,
                    message=message,
                )
                session.add(alert)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return False

    async def get_device_alerts(
        self,
        device_id: str,
        alert_type: Optional[str] = None,
        level: Optional[str] = None,
        is_resolved: Optional[bool] = None,
    ) -> List[Dict]:
        """获取设备告警"""
        try:
            async with self.transaction.transaction() as session:
                alerts = await DeviceAlert.get_device_alerts(
                    session, device_id, alert_type, level, is_resolved
                )
                return [alert.to_dict() for alert in alerts]
        except Exception as e:
            logger.error(f"Error getting device alerts: {e}")
            return []

    @staticmethod
    async def get_monitor_stats(device_id: str):
        async with get_session() as session:
            query = select(Monitor).where(
                Monitor.device_id == device_id, Monitor.enabled == True
            )
            result = await session.execute(query)
            return result.scalars().all()


# 创建全局监控服务实例
monitor_service = MonitorService()
