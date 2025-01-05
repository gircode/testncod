"""告警系统"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.slave.monitor.collector import metrics_collector

logger = setup_logger("alert_system")


@dataclass
class AlertRule:
    """告警规则"""

    name: str
    metric_path: str  # 如 "system.cpu_usage"
    threshold: float
    comparison: str  # "gt", "lt", "eq"
    severity: str  # "info", "warning", "error", "critical"
    description: str


@dataclass
class Alert:
    """告警信息"""

    rule_name: str
    metric_path: str
    current_value: float
    threshold: float
    severity: str
    description: str
    timestamp: datetime


class AlertSystem:
    """告警系统"""

    def __init__(self):
        self.collector = metrics_collector
        self.running = False
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self._load_rules()

    def _load_rules(self):
        """加载告警规则"""
        self.rules = [
            AlertRule(
                name="high_cpu_usage",
                metric_path="system.cpu_usage",
                threshold=80.0,
                comparison="gt",
                severity="warning",
                description="CPU使用率过高",
            ),
            AlertRule(
                name="high_memory_usage",
                metric_path="system.memory_usage",
                threshold=85.0,
                comparison="gt",
                severity="warning",
                description="内存使用率过高",
            ),
            AlertRule(
                name="high_device_usage",
                metric_path="devices.active_devices",
                threshold=90.0,
                comparison="gt",
                severity="warning",
                description="设备使用率过高",
            ),
        ]

    async def start(self):
        """启动告警系统"""
        try:
            self.running = True
            asyncio.create_task(self._alert_check_loop())
            logger.info("Alert system started")
        except Exception as e:
            logger.error(f"Error starting alert system: {e}")
            raise

    async def stop(self):
        """停止告警系统"""
        try:
            self.running = False
            logger.info("Alert system stopped")
        except Exception as e:
            logger.error(f"Error stopping alert system: {e}")

    def _get_metric_value(self, metric_path: str) -> Optional[float]:
        """获取指标值"""
        try:
            metrics = self.collector.get_current_metrics()
            parts = metric_path.split(".")
            value = metrics
            for part in parts:
                value = value.get(part)
                if value is None:
                    return None
            return float(value)
        except Exception as e:
            logger.error(f"Error getting metric value: {e}")
            return None

    def _check_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        """检查阈值"""
        if comparison == "gt":
            return value > threshold
        elif comparison == "lt":
            return value < threshold
        elif comparison == "eq":
            return abs(value - threshold) < 0.001
        return False

    async def _check_rule(self, rule: AlertRule):
        """检查规则"""
        try:
            value = self._get_metric_value(rule.metric_path)
            if value is None:
                return

            is_triggered = self._check_threshold(value, rule.threshold, rule.comparison)

            if is_triggered and rule.name not in self.active_alerts:
                # 创建新告警
                alert = Alert(
                    rule_name=rule.name,
                    metric_path=rule.metric_path,
                    current_value=value,
                    threshold=rule.threshold,
                    severity=rule.severity,
                    description=rule.description,
                    timestamp=datetime.utcnow(),
                )
                self.active_alerts[rule.name] = alert
                self.alert_history.append(alert)
                await self._notify_alert(alert)

            elif not is_triggered and rule.name in self.active_alerts:
                # 解除告警
                del self.active_alerts[rule.name]
                logger.info(f"Alert resolved: {rule.name}")

        except Exception as e:
            logger.error(f"Error checking rule {rule.name}: {e}")

    async def _alert_check_loop(self):
        """告警检查循环"""
        while self.running:
            try:
                for rule in self.rules:
                    await self._check_rule(rule)
                await asyncio.sleep(config.alert_check_interval)
            except Exception as e:
                logger.error(f"Error in alert check loop: {e}")
                await asyncio.sleep(5)

    async def _notify_alert(self, alert: Alert):
        """通知告警"""
        try:
            logger.warning(
                f"Alert triggered: {alert.rule_name} - "
                f"Current value: {alert.current_value} - "
                f"Threshold: {alert.threshold} - "
                f"Severity: {alert.severity}"
            )
            # 这里可以添加其他通知方式，如邮件、短信等
        except Exception as e:
            logger.error(f"Error notifying alert: {e}")

    def get_active_alerts(self) -> List[Alert]:
        """获取活动告警"""
        return list(self.active_alerts.values())

    def get_alert_history(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> List[Alert]:
        """获取告警历史"""
        try:
            alerts = self.alert_history
            if start_time:
                alerts = [a for a in alerts if a.timestamp >= start_time]
            if end_time:
                alerts = [a for a in alerts if a.timestamp <= end_time]
            return alerts
        except Exception as e:
            logger.error(f"Error getting alert history: {e}")
            return []


# 创建全局告警系统实例
alert_system = AlertSystem()
