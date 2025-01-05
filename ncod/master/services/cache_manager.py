from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import asyncio
import logging
from cachetools import TTLCache, LRUCache
from ncod.master.services.cache_monitor import CacheMonitor
import time

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(self):
        # 短期缓存(5分钟)
        self.short_term = TTLCache(maxsize=1000, ttl=300)
        # 长期缓存(1小时)
        self.long_term = TTLCache(maxsize=500, ttl=3600)
        # 统计数据缓存(10分钟)
        self.stats_cache = TTLCache(maxsize=200, ttl=600)
        # 用户会话缓存
        self.session_cache = LRUCache(maxsize=100)

        # 启动清理任务
        asyncio.create_task(self._cleanup_loop())

        self.monitor = CacheMonitor()

    async def get_or_set(
        self, cache_type: str, key: str, getter_func, ttl: Optional[int] = None
    ) -> Any:
        """获取或设置缓存"""
        start_time = time.time()
        cache = self._get_cache(cache_type)

        if not cache:
            return await getter_func()

        # 尝试获取缓存
        try:
            value = cache.get(key)
            if value is not None:
                self.monitor.record_hit(cache_type, time.time() - start_time)
                return value
        except Exception as e:
            logger.error(f"Cache get error: {e}")

        # 缓存未命中
        self.monitor.record_miss(cache_type, time.time() - start_time)

        # 获取新数据
        value = await getter_func()

        # 设置缓存
        try:
            if ttl:
                cache[key] = {
                    "value": value,
                    "expires": datetime.utcnow() + timedelta(seconds=ttl),
                }
            else:
                cache[key] = value
        except Exception as e:
            logger.error(f"Cache set error: {e}")

        return value

    def invalidate(self, cache_type: str, key: str):
        """使缓存失效"""
        cache = self._get_cache(cache_type)
        if cache and key in cache:
            del cache[key]

    def clear_all(self):
        """清除所有缓存"""
        self.short_term.clear()
        self.long_term.clear()
        self.stats_cache.clear()
        self.session_cache.clear()

    def _get_cache(self, cache_type: str) -> Optional[Dict]:
        """获取指定类型的缓存"""
        return {
            "short": self.short_term,
            "long": self.long_term,
            "stats": self.stats_cache,
            "session": self.session_cache,
        }.get(cache_type)

    async def _cleanup_loop(self):
        """定期清理过期缓存"""
        while True:
            try:
                self._cleanup_expired()
                await asyncio.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    def _cleanup_expired(self):
        """清理过期缓存"""
        start_time = time.time()
        now = datetime.utcnow()
        eviction_count = 0

        for cache in [self.short_term, self.long_term, self.stats_cache]:
            expired_keys = [
                key
                for key, value in cache.items()
                if isinstance(value, dict)
                and value.get("expires")
                and value["expires"] < now
            ]

            for key in expired_keys:
                del cache[key]
                eviction_count += 1

        duration = time.time() - start_time
        self.monitor.record_cleanup(duration)
        if eviction_count > 0:
            self.monitor.record_eviction()

    def get_metrics(self) -> Dict:
        """获取缓存指标"""
        return self.monitor.get_current_metrics()

    def get_metrics_history(self) -> List[Dict]:
        """获取历史指标"""
        return self.monitor.get_history()
