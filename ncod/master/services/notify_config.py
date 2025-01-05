"""通知配置服务"""

from typing import Dict, List, Optional
from ncod.core.logger import setup_logger
from ncod.core.db.transaction import transaction_manager
from ncod.master.models.notify_config import NotifyConfig
from ncod.core.cache.manager import cache_manager

logger = setup_logger("notify_config")


class NotifyConfigService:
    """通知配置服务"""

    def __init__(self):
        self.transaction = transaction_manager
        self.cache = cache_manager
        self.cache_ttl = 300  # 5分钟

    async def create_config(self, data: Dict) -> Optional[Dict]:
        """创建通知配置"""
        try:
            async with self.transaction.transaction() as session:
                config = NotifyConfig(
                    name=data["name"],
                    channel=data["channel"],
                    config=data["config"],
                    description=data.get("description"),
                )
                session.add(config)
                await session.commit()

                # 清除缓存
                cache_key = f"notify_configs:{data['channel']}"
                await self.cache.delete(cache_key)

                return config.to_dict()
        except Exception as e:
            logger.error(f"Error creating notify config: {e}")
            return None

    async def get_channel_configs(self, channel: Optional[str] = None) -> List[Dict]:
        """获取通知配置"""
        try:
            # 尝试从缓存获取
            cache_key = f"notify_configs:{channel}" if channel else "notify_configs:all"
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

            async with self.transaction.transaction() as session:
                configs = await NotifyConfig.get_channel_configs(session, channel)
                result = [config.to_dict() for config in configs]

                # 设置缓存
                await self.cache.set(cache_key, result, self.cache_ttl)
                return result
        except Exception as e:
            logger.error(f"Error getting notify configs: {e}")
            return []

    async def update_config(self, config_id: str, data: Dict) -> Optional[Dict]:
        """更新通知配置"""
        try:
            async with self.transaction.transaction() as session:
                config = await session.get(NotifyConfig, config_id)
                if not config:
                    return None

                # 更新字段
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

                await session.commit()

                # 清除缓存
                cache_key = f"notify_configs:{config.channel}"
                await self.cache.delete(cache_key)
                await self.cache.delete("notify_configs:all")

                return config.to_dict()
        except Exception as e:
            logger.error(f"Error updating notify config: {e}")
            return None

    async def delete_config(self, config_id: str) -> bool:
        """删除通知配置"""
        try:
            async with self.transaction.transaction() as session:
                config = await session.get(NotifyConfig, config_id)
                if not config:
                    return False

                await session.delete(config)
                await session.commit()

                # 清除缓存
                cache_key = f"notify_configs:{config.channel}"
                await self.cache.delete(cache_key)
                await self.cache.delete("notify_configs:all")

                return True
        except Exception as e:
            logger.error(f"Error deleting notify config: {e}")
            return False


# 创建全局通知配置服务实例
notify_config_service = NotifyConfigService()
