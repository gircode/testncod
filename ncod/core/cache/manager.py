"""缓存管理器"""

import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import aioredis
from functools import wraps
from ncod.core.config import config
from ncod.core.logger import setup_logger

logger = setup_logger("cache_manager")


class CacheManager:
    """缓存管理器"""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.local_cache: Dict[str, Dict[str, Any]] = {}

    async def init_cache(self):
        """初始化缓存"""
        try:
            self.redis = await aioredis.from_url(
                config.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=config.redis_pool_size,
            )
            logger.info("Cache manager initialized")
        except Exception as e:
            logger.error(f"Error initializing cache: {e}")
            raise

    async def close(self):
        """关闭缓存连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Cache connections closed")

    async def get(self, key: str, use_local: bool = True) -> Optional[Any]:
        """获取缓存值"""
        try:
            # 检查本地缓存
            if use_local and key in self.local_cache:
                cache_data = self.local_cache[key]
                if cache_data["expire_at"] > datetime.utcnow():
                    return cache_data["value"]
                else:
                    del self.local_cache[key]

            # 检查Redis缓存
            if self.redis:
                value = await self.redis.get(key)
                if value and use_local:
                    # 更新本地缓存
                    ttl = await self.redis.ttl(key)
                    if ttl > 0:
                        self.local_cache[key] = {
                            "value": value,
                            "expire_at": datetime.utcnow() + timedelta(seconds=ttl),
                        }
                return value
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, use_local: bool = True
    ) -> bool:
        """设置缓存值"""
        try:
            # 设置Redis缓存
            if self.redis:
                if ttl:
                    await self.redis.setex(key, ttl, value)
                else:
                    await self.redis.set(key, value)

            # 设置本地缓存
            if use_local:
                expire_at = (
                    datetime.utcnow() + timedelta(seconds=ttl)
                    if ttl
                    else datetime.utcnow() + timedelta(hours=1)
                )
                self.local_cache[key] = {"value": value, "expire_at": expire_at}
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            # 删除本地缓存
            if key in self.local_cache:
                del self.local_cache[key]

            # 删除Redis缓存
            if self.redis:
                await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

    def cache(
        self, ttl: Optional[int] = None, use_local: bool = True, key_prefix: str = ""
    ):
        """缓存装饰器"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = (
                    f"{key_prefix}:{func.__name__}:" f"{str(args)}:{str(kwargs)}"
                )

                # 尝试获取缓存
                cached_value = await self.get(cache_key, use_local=use_local)
                if cached_value is not None:
                    return cached_value

                # 执行函数
                result = await func(*args, **kwargs)

                # 设置缓存
                await self.set(cache_key, result, ttl, use_local)

                return result

            return wrapper

        return decorator


# 创建全局缓存管理器实例
cache_manager = CacheManager()
