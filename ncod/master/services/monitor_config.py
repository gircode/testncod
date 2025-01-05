"""监控配置服务"""

from typing import Dict, List, Optional
from ncod.core.logger import setup_logger
from ncod.core.db.transaction import transaction_manager
from ncod.master.models.monitor_config import MonitorConfig
from ncod.core.cache.manager import cache_manager

logger = setup_logger("monitor_config")


class MonitorConfigService:
    """监控配置服务"""

    def __init__(self):
        self.transaction = transaction_manager
        self.cache = cache_manager
        self.cache_ttl = 300  # 5分钟

    async def create_config(self, device_id: str, data: Dict) -> Optional[Dict]:
        """创建监控配置"""
        try:
            async with self.transaction.transaction() as session:
                config = MonitorConfig(
                    device_id=device_id,
                    metric_type=data["metric_type"],
                    enabled=data.get("enabled", True),
                    threshold=data.get("threshold"),
                    interval=data.get("interval", 30),
                    alert_levels=data.get("alert_levels", {}),
                    description=data.get("description"),
                )
                session.add(config)
                await session.commit()

                # 清除缓存
                cache_key = f"monitor_configs:{device_id}"
                await self.cache.delete(cache_key)

                return config.to_dict()
        except Exception as e:
            logger.error(f"Error creating monitor config: {e}")
            return None

    async def get_device_configs(self, device_id: str) -> List[Dict]:
        """获取设备监控配置"""
        try:
            # 尝试从缓存获取
            cache_key = f"monitor_configs:{device_id}"
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

            async with self.transaction.transaction() as session:
                configs = await MonitorConfig.get_device_configs(session, device_id)
                result = [config.to_dict() for config in configs]

                # 设置缓存
                await self.cache.set(cache_key, result, self.cache_ttl)
                return result
        except Exception as e:
            logger.error(f"Error getting device configs: {e}")
            return []

    async def update_config(self, config_id: str, data: Dict) -> Optional[Dict]:
        """更新监控配置"""
        try:
            async with self.transaction.transaction() as session:
                config = await session.get(MonitorConfig, config_id)
                if not config:
                    return None

                # 更新字段
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

                await session.commit()

                # 清除缓存
                cache_key = f"monitor_configs:{config.device_id}"
                await self.cache.delete(cache_key)

                return config.to_dict()
        except Exception as e:
            logger.error(f"Error updating monitor config: {e}")
            return None


# 创建全局监控配置服务实例
monitor_config_service = MonitorConfigService()
