"""Cache Optimizer模块"""

import asyncio
import hashlib
import json
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

import aioredis
from cachetools import LRUCache, TTLCache

from ..config import settings
from .performance import performance_monitor


class CacheStrategyOptimizer:
    """缓存策略优化器"""

    def __init__(self):
        # 内存缓存
        self.memory_cache = TTLCache(maxsize=1000, ttl=300)  # 5分钟缓存
        self.lru_cache = LRUCache(maxsize=100)  # 最近使用的100个项目

        # Redis连接
        self.redis = None
        self.redis_prefix = "ncod:"

        # 缓存统计
        self.cache_stats = {"hits": 0, "misses": 0, "memory_size": 0, "redis_size": 0}

    async def initialize(self):
        """初始化Redis连接"""
        if not self.redis:
            self.redis = await aioredis.create_redis_pool(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
            )

    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()

    async def get_or_set(
        self, key: str, func: Callable, ttl: int = 300, strategy: str = "memory"
    ) -> Any:
        """获取或设置缓存"""
        cache_key = self._generate_cache_key(key)

        # 尝试从缓存获取
        cached_value = await self._get_from_cache(cache_key, strategy)
        if cached_value is not None:
            self.cache_stats["hits"] += 1
            return cached_value

        self.cache_stats["misses"] += 1

        # 执行函数获取新值
        value = await func()

        # 设置缓存
        await self._set_to_cache(cache_key, value, ttl, strategy)

        return value

    async def invalidate(self, key: str, strategy: str = "all"):
        """失效缓存"""
        cache_key = self._generate_cache_key(key)

        if strategy in ["all", "memory"]:
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            if cache_key in self.lru_cache:
                del self.lru_cache[cache_key]

        if strategy in ["all", "redis"] and self.redis:
            await self.redis.delete(f"{self.redis_prefix}{cache_key}")

    async def clear(self, strategy: str = "all"):
        """清除所有缓存"""
        if strategy in ["all", "memory"]:
            self.memory_cache.clear()
            self.lru_cache.clear()

        if strategy in ["all", "redis"] and self.redis:
            await self.redis.flushdb()

    def _generate_cache_key(self, key: str) -> str:
        """生成缓存键"""
        if isinstance(key, (dict, list)):
            key = json.dumps(key, sort_keys=True)
        return hashlib.md5(str(key).encode()).hexdigest()

    async def _get_from_cache(self, key: str, strategy: str) -> Optional[Any]:
        """从缓存获取值"""
        if strategy == "memory":
            # 先检查LRU缓存
            if key in self.lru_cache:
                return self.lru_cache[key]
            # 再检查TTL缓存
            return self.memory_cache.get(key)

        elif strategy == "redis" and self.redis:
            value = await self.redis.get(f"{self.redis_prefix}{key}")
            if value:
                return pickle.loads(value)

        return None

    async def _set_to_cache(self, key: str, value: Any, ttl: int, strategy: str):
        """设置缓存值"""
        if strategy == "memory":
            self.memory_cache[key] = value
            self.lru_cache[key] = value
            self.cache_stats["memory_size"] = len(self.memory_cache)

        elif strategy == "redis" and self.redis:
            await self.redis.setex(
                f"{self.redis_prefix}{key}", ttl, pickle.dumps(value)
            )
            self.cache_stats["redis_size"] = await self.redis.dbsize()

    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        return self.cache_stats.copy()


class CacheDecorator:
    """缓存装饰器"""

    def __init__(self, cache_optimizer: CacheStrategyOptimizer):
        self.cache_optimizer = cache_optimizer

    def cache(
        self, ttl: int = 300, strategy: str = "memory", key_generator: Callable = None
    ):
        """缓存装饰器"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                if key_generator:
                    cache_key = key_generator(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

                return await self.cache_optimizer.get_or_set(
                    cache_key, lambda: func(*args, **kwargs), ttl, strategy
                )

            return wrapper

        return decorator


class CacheWarmer:
    """缓存预热器"""

    def __init__(self, cache_optimizer: CacheStrategyOptimizer):
        self.cache_optimizer = cache_optimizer
        self.warm_up_tasks = {}

    def register_task(
        self, name: str, func: Callable, ttl: int = 300, strategy: str = "memory"
    ):
        """注册预热任务"""
        self.warm_up_tasks[name] = {"func": func, "ttl": ttl, "strategy": strategy}

    async def warm_up(self, task_names: List[str] = None):
        """执行预热"""
        if task_names is None:
            task_names = list(self.warm_up_tasks.keys())

        for name in task_names:
            if name in self.warm_up_tasks:
                task = self.warm_up_tasks[name]
                await self.cache_optimizer.get_or_set(
                    f"warm_up:{name}", task["func"], task["ttl"], task["strategy"]
                )


class CacheMonitor:
    """缓存监控器"""

    def __init__(self, cache_optimizer: CacheStrategyOptimizer):
        self.cache_optimizer = cache_optimizer
        self.monitoring_data = []

    async def collect_metrics(self):
        """收集缓存指标"""
        stats = self.cache_optimizer.get_cache_stats()
        self.monitoring_data.append({"timestamp": datetime.now(), "stats": stats})

        # 记录性能指标
        hit_rate = (
            stats["hits"] / (stats["hits"] + stats["misses"])
            if (stats["hits"] + stats["misses"]) > 0
            else 0
        )
        performance_monitor.record_metric("cache_hit_rate", hit_rate)
        performance_monitor.record_metric("cache_memory_size", stats["memory_size"])
        performance_monitor.record_metric("cache_redis_size", stats["redis_size"])

    def get_monitoring_data(self, hours: int = 24) -> List[Dict]:
        """获取监控数据"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            data for data in self.monitoring_data if data["timestamp"] >= cutoff_time
        ]


# 创建全局实例
cache_optimizer = CacheStrategyOptimizer()
cache_decorator = CacheDecorator(cache_optimizer)
cache_warmer = CacheWarmer(cache_optimizer)
cache_monitor = CacheMonitor(cache_optimizer)
