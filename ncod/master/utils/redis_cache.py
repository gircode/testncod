from typing import Any, Optional
import redis
from flask_caching import Cache
from ..config import Config

# 创建Redis连接
redis_client = redis.Redis.from_url(Config.REDIS_URL)

# 创建Flask-Caching实例
cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': Config.REDIS_URL,
    'CACHE_DEFAULT_TIMEOUT': 300
})

def init_cache(app):
    """初始化缓存"""
    cache.init_app(app)

def set_cache(key: str, value: Any, timeout: Optional[int] = None) -> bool:
    """设置缓存"""
    try:
        return cache.set(key, value, timeout=timeout)
    except Exception as e:
        app.logger.error(f"Cache set error: {e}")
        return False

def get_cache(key: str) -> Any:
    """获取缓存"""
    try:
        return cache.get(key)
    except Exception as e:
        app.logger.error(f"Cache get error: {e}")
        return None

def delete_cache(key: str) -> bool:
    """删除缓存"""
    try:
        return cache.delete(key)
    except Exception as e:
        app.logger.error(f"Cache delete error: {e}")
        return False

def clear_cache() -> bool:
    """清除所有缓存"""
    try:
        return cache.clear()
    except Exception as e:
        app.logger.error(f"Cache clear error: {e}")
        return False 