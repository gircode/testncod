"""
配置缓存预热服务
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.monitoring import log_db_query
from ..models.config import SystemConfig

logger = logging.getLogger(__name__)


class ConfigCache:
    """配置缓存管理器"""

    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._group_cache: Dict[str, Set[str]] = {}
        self._last_update = datetime.min
        self._is_warming_up = False
        self._warmup_interval = timedelta(minutes=5)

    @property
    def is_warmed_up(self) -> bool:
        """缓存是否已预热"""
        return bool(self._cache)

    @property
    def cache_age(self) -> timedelta:
        """缓存年龄"""
        return datetime.utcnow() - self._last_update

    def get(self, key: str) -> Optional[Dict]:
        """获取配置"""
        return self._cache.get(key)

    def get_by_group(self, group: str) -> List[Dict]:
        """获取组内配置"""
        if group not in self._group_cache:
            return []
        return [
            self._cache[key] for key in self._group_cache[group] if key in self._cache
        ]

    @log_db_query
    async def warmup(self, db: Session):
        """预热缓存"""
        if self._is_warming_up:
            logger.warning("缓存预热正在进行中")
            return

        try:
            self._is_warming_up = True

            # 构建查询
            query = select(SystemConfig).order_by(SystemConfig.key)

            # 执行查询
            result = await db.execute(query)
            configs = result.scalars().all()

            # 更新缓存
            new_cache = {}
            new_group_cache: Dict[str, Set[str]] = {}

            for config in configs:
                # 缓存配置
                new_cache[config.key] = {
                    "key": config.key,
                    "value": config.value,
                    "type": config.type,
                    "group": config.group,
                    "is_public": config.is_public,
                    "updated_at": config.updated_at,
                }

                # 更新组缓存
                if config.group:
                    if config.group not in new_group_cache:
                        new_group_cache[config.group] = set()
                    new_group_cache[config.group].add(config.key)

            # 原子性更新缓存
            self._cache = new_cache
            self._group_cache = new_group_cache
            self._last_update = datetime.utcnow()

            logger.info(f"缓存预热完成，共加载 {len(self._cache)} 个配置")

        except Exception as e:
            logger.error(f"缓存预热失败: {str(e)}")
            raise

        finally:
            self._is_warming_up = False

    async def start_warmup_task(self, db: Session):
        """启动定期预热任务"""
        while True:
            try:
                # 检查缓存是否需要更新
                if not self.is_warmed_up or self.cache_age > self._warmup_interval:
                    await self.warmup(db)

            except Exception as e:
                logger.error(f"定期预热任务失败: {str(e)}")

            await asyncio.sleep(60)  # 每分钟检查一次

    def update_cache(self, config: SystemConfig):
        """更新单个配置的缓存"""
        try:
            # 更新配置缓存
            self._cache[config.key] = {
                "key": config.key,
                "value": config.value,
                "type": config.type,
                "group": config.group,
                "is_public": config.is_public,
                "updated_at": config.updated_at,
            }

            # 更新组缓存
            if config.group:
                if config.group not in self._group_cache:
                    self._group_cache[config.group] = set()
                self._group_cache[config.group].add(config.key)

            logger.debug(f"配置缓存已更新: {config.key}")

        except Exception as e:
            logger.error(f"更新配置缓存失败: {str(e)}")

    def remove_from_cache(self, key: str):
        """从缓存中移除配置"""
        try:
            if key in self._cache:
                config = self._cache[key]

                # 从组缓存中移除
                if config["group"] and config["group"] in self._group_cache:
                    self._group_cache[config["group"]].discard(key)

                # 从配置缓存中移除
                del self._cache[key]

                logger.debug(f"配置已从缓存中移除: {key}")

        except Exception as e:
            logger.error(f"从缓存中移除配置失败: {str(e)}")

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        self._group_cache.clear()
        self._last_update = datetime.min
        logger.info("缓存已清空")


# 创建全局缓存管理器实例
config_cache = ConfigCache()
