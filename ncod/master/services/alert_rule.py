"""告警规则服务"""

from typing import Dict, List, Optional
from ncod.core.logger import setup_logger
from ncod.core.db.transaction import transaction_manager
from ncod.master.models.alert_rule import AlertRule
from ncod.core.cache.manager import cache_manager

logger = setup_logger("alert_rule")


class AlertRuleService:
    """告警规则服务"""

    def __init__(self):
        self.transaction = transaction_manager
        self.cache = cache_manager
        self.cache_ttl = 300  # 5分钟

    async def create_rule(self, device_id: str, data: Dict) -> Optional[Dict]:
        """创建告警规则"""
        try:
            async with self.transaction.transaction() as session:
                rule = AlertRule(
                    device_id=device_id,
                    name=data["name"],
                    metric_type=data["metric_type"],
                    condition=data["condition"],
                    threshold=data["threshold"],
                    level=data["level"],
                    enabled=data.get("enabled", True),
                    notify_channels=data.get("notify_channels", {}),
                    description=data.get("description"),
                )
                session.add(rule)
                await session.commit()

                # 清除缓存
                cache_key = f"alert_rules:{device_id}"
                await self.cache.delete(cache_key)

                return rule.to_dict()
        except Exception as e:
            logger.error(f"Error creating alert rule: {e}")
            return None

    async def get_device_rules(
        self, device_id: str, enabled: Optional[bool] = None
    ) -> List[Dict]:
        """获取设备告警规则"""
        try:
            # 尝试从缓存获取
            cache_key = f"alert_rules:{device_id}"
            cached = await self.cache.get(cache_key)
            if cached and enabled is None:
                return cached

            async with self.transaction.transaction() as session:
                rules = await AlertRule.get_device_rules(session, device_id, enabled)
                result = [rule.to_dict() for rule in rules]

                # 设置缓存(仅缓存全部规则)
                if enabled is None:
                    await self.cache.set(cache_key, result, self.cache_ttl)
                return result
        except Exception as e:
            logger.error(f"Error getting device rules: {e}")
            return []

    async def update_rule(self, rule_id: str, data: Dict) -> Optional[Dict]:
        """更新告警规则"""
        try:
            async with self.transaction.transaction() as session:
                rule = await session.get(AlertRule, rule_id)
                if not rule:
                    return None

                # 更新字段
                for key, value in data.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)

                await session.commit()

                # 清除缓存
                cache_key = f"alert_rules:{rule.device_id}"
                await self.cache.delete(cache_key)

                return rule.to_dict()
        except Exception as e:
            logger.error(f"Error updating alert rule: {e}")
            return None

    async def delete_rule(self, rule_id: str) -> bool:
        """删除告警规则"""
        try:
            async with self.transaction.transaction() as session:
                rule = await session.get(AlertRule, rule_id)
                if not rule:
                    return False

                await session.delete(rule)
                await session.commit()

                # 清除缓存
                cache_key = f"alert_rules:{rule.device_id}"
                await self.cache.delete(cache_key)

                return True
        except Exception as e:
            logger.error(f"Error deleting alert rule: {e}")
            return False


# 创建全局告警规则服务实例
alert_rule_service = AlertRuleService()
