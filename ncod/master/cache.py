import json
from typing import Any, Optional, Union
from redis.asyncio import Redis, ConnectionPool
from .config.settings import REDIS_CONFIG

# 创建Redis连接池
pool = ConnectionPool(
    host=REDIS_CONFIG["host"],
    port=REDIS_CONFIG["port"],
    db=REDIS_CONFIG["db"],
    password=REDIS_CONFIG["password"],
    decode_responses=True,
    encoding="utf-8",
)

# 创建Redis客户端
redis = Redis(connection_pool=pool)


class CacheManager:
    """缓存管理器"""

    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = await redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    @staticmethod
    async def set(key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存"""
        try:
            value = json.dumps(value)
            if expire:
                await redis.setex(key, expire, value)
            else:
                await redis.set(key, value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    @staticmethod
    async def delete(key: str) -> bool:
        """删除缓存"""
        try:
            await redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    @staticmethod
    async def exists(key: str) -> bool:
        """检查缓存是否存在"""
        try:
            return await redis.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

    @staticmethod
    async def ttl(key: str) -> int:
        """获取缓存过期时间"""
        try:
            return await redis.ttl(key)
        except Exception as e:
            print(f"Cache ttl error: {e}")
            return -1

    @staticmethod
    async def incr(key: str) -> int:
        """递增计数器"""
        try:
            return await redis.incr(key)
        except Exception as e:
            print(f"Cache incr error: {e}")
            return 0

    @staticmethod
    async def decr(key: str) -> int:
        """递减计数器"""
        try:
            return await redis.decr(key)
        except Exception as e:
            print(f"Cache decr error: {e}")
            return 0

    @staticmethod
    async def hset(name: str, key: str, value: Any) -> bool:
        """设置哈希表字段"""
        try:
            value = json.dumps(value)
            await redis.hset(name, key, value)
            return True
        except Exception as e:
            print(f"Cache hset error: {e}")
            return False

    @staticmethod
    async def hget(name: str, key: str) -> Optional[Any]:
        """获取哈希表字段"""
        try:
            value = await redis.hget(name, key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache hget error: {e}")
            return None

    @staticmethod
    async def hdel(name: str, key: str) -> bool:
        """删除哈希表字段"""
        try:
            await redis.hdel(name, key)
            return True
        except Exception as e:
            print(f"Cache hdel error: {e}")
            return False

    @staticmethod
    async def clear() -> bool:
        """清空所有缓存"""
        try:
            await redis.flushdb()
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False
