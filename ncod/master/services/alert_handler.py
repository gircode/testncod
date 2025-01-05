"""告警处理服务"""

from typing import Dict, List
from datetime import datetime
from sqlalchemy.sql import select

from ncod.core.logger import LoggerManager
from ncod.core.db.transaction import TransactionManager
from ncod.core.db.pool import DatabasePool
from ncod.master.services.notify import NotifyService
from ncod.master.services.notify_config import NotifyConfigService
from ncod.master.models.alert_rule import AlertRule

logger = LoggerManager.get_logger(__name__)


class AlertHandler:
    """告警处理器"""

    def __init__(self, db_pool: DatabasePool):
        self.notify_service = NotifyService()
        self.notify_config_service = NotifyConfigService()
        self.transaction = TransactionManager(db_pool)

    async def check_metric(
        self, device_id: str, metric_type: str, value: float
    ) -> List[Dict]:
        """检查指标是否触发告警规则"""
        alerts = []
        async with self.transaction.transaction() as session:
            # 获取活跃的告警规则
            query = (
                select(AlertRule)
                .where(AlertRule.metric_type == metric_type)
                .where(AlertRule.enabled.is_(True))
            )
            result = await session.execute(query)
            rules = result.scalars().all()

            for rule in rules:
                # 从数据库模型中获取实际值
                condition = str(getattr(rule, "condition", ""))
                threshold = float(getattr(rule, "threshold", 0.0))
                channels = getattr(rule, "notify_channels", None)
                notify_channels = list(channels) if channels is not None else []

                if self._check_condition(value, condition, threshold):
                    alert = {
                        "device_id": device_id,
                        "rule_id": str(getattr(rule, "id", "")),
                        "metric_type": metric_type,
                        "value": value,
                        "timestamp": datetime.now(),
                    }
                    alerts.append(alert)
                    # 发送通知
                    await self._send_notifications(alert, notify_channels)

        return alerts

    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        """检查条件"""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return value == threshold
        else:
            return False

    async def _send_notifications(self, alert: Dict, channels: List[str]) -> None:
        """发送通知"""
        try:
            # 获取通知配置
            configs = await self.notify_config_service.get_channel_configs()
            channel_configs = {
                config["channel"]: config["config"] for config in configs
            }

            # 发送通知
            for channel in channels:
                if channel not in channel_configs:
                    continue

                # 构造通知消息
                message = (
                    f"告警: 设备 {alert['device_id']} "
                    f"指标 {alert['metric_type']} "
                    f"当前值 {alert['value']}"
                )

                await self.notify_service.send_notification(
                    channel, channel_configs[channel], message
                )
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")


def create_alert_handler(db_pool: DatabasePool) -> AlertHandler:
    """创建告警处理器实例"""
    return AlertHandler(db_pool)
