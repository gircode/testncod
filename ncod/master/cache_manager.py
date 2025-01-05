import json
from typing import Dict, List, Optional, Any, Union
from redis import Redis, ConnectionPool
from .utils.logger import get_logger
from .config_manager import ConfigManager

logger = get_logger(__name__)
config = ConfigManager()


class CacheManager:
    _instance: Optional['CacheManager'] = None
    _redis: Optional[Redis] = None
    _pool: Optional[ConnectionPool] = None
    
    def __new__(cls) -> 'CacheManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if not self._redis:
            self._init_redis()
    
    def _init_redis(self) -> None:
        """初始化Redis连接"""
        try:
            if not self._pool:
                self._pool = ConnectionPool(
                    host=config.get('redis.host', 'localhost'),
                    port=config.get('redis.port', 6379),
                    db=config.get('redis.db', 0),
                    password=config.get('redis.password', None),
                    decode_responses=True
                )
                
            self._redis = Redis(connection_pool=self._pool)
            logger.info("Redis connection initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise
    
    def _ensure_redis(self) -> None:
        """确保Redis连接可用"""
        try:
            if not self._redis:
                self._init_redis()
            else:
                self._redis.ping()
                
        except Exception:
            self._init_redis()
    
    def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """获取缓存值"""
        try:
            self._ensure_redis()
            value = self._redis.get(key)
            
            if value is None:
                return default
                
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"Failed to get cache value for {key}: {e}")
            return default
    
    def set(
        self,
        key: str,
        value: Any,
        timeout: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            self._ensure_redis()
            
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
                
            if timeout:
                return bool(self._redis.setex(key, timeout, value))
            else:
                return bool(self._redis.set(key, value))
                
        except Exception as e:
            logger.error(f"Failed to set cache value for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            self._ensure_redis()
            return bool(self._redis.delete(key))
            
        except Exception as e:
            logger.error(f"Failed to delete cache value for {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            self._ensure_redis()
            return bool(self._redis.exists(key))
            
        except Exception as e:
            logger.error(f"Failed to check cache existence for {key}: {e}")
            return False
    
    def keys(self, pattern: str = '*') -> List[str]:
        """获取匹配的缓存键"""
        try:
            self._ensure_redis()
            return self._redis.keys(pattern)
            
        except Exception as e:
            logger.error(f"Failed to get cache keys for {pattern}: {e}")
            return []
    
    def flush(self) -> bool:
        """清空所有缓存"""
        try:
            self._ensure_redis()
            self._redis.flushdb()
            logger.info("Cache flushed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to flush cache: {e}")
            return False
    
    def get_multiple(
        self,
        keys: List[str],
        default: Any = None
    ) -> Dict[str, Any]:
        """批量获取缓存值"""
        try:
            self._ensure_redis()
            values = self._redis.mget(keys)
            
            result = {}
            for key, value in zip(keys, values):
                if value is None:
                    result[key] = default
                else:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
                        
            return result
            
        except Exception as e:
            logger.error(f"Failed to get multiple cache values: {e}")
            return {key: default for key in keys}
    
    def set_multiple(
        self,
        mapping: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> bool:
        """批量设置缓存值"""
        try:
            self._ensure_redis()
            
            # 处理需要JSON序列化的值
            processed_mapping = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    processed_mapping[key] = json.dumps(value)
                else:
                    processed_mapping[key] = value
                    
            if timeout:
                pipe = self._redis.pipeline()
                for key, value in processed_mapping.items():
                    pipe.setex(key, timeout, value)
                pipe.execute()
            else:
                self._redis.mset(processed_mapping)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to set multiple cache values: {e}")
            return False
    
    def delete_multiple(self, keys: List[str]) -> bool:
        """批量删除缓存值"""
        try:
            self._ensure_redis()
            self._redis.delete(*keys)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete multiple cache values: {e}")
            return False
    
    def increment(
        self,
        key: str,
        amount: Union[int, float] = 1
    ) -> Optional[Union[int, float]]:
        """增加缓存值"""
        try:
            self._ensure_redis()
            
            if isinstance(amount, float):
                return self._redis.incrbyfloat(key, amount)
            else:
                return self._redis.incrby(key, amount)
                
        except Exception as e:
            logger.error(f"Failed to increment cache value for {key}: {e}")
            return None
    
    def decrement(
        self,
        key: str,
        amount: Union[int, float] = 1
    ) -> Optional[Union[int, float]]:
        """减少缓存值"""
        try:
            self._ensure_redis()
            
            if isinstance(amount, float):
                return self._redis.incrbyfloat(key, -amount)
            else:
                return self._redis.decrby(key, amount)
                
        except Exception as e:
            logger.error(f"Failed to decrement cache value for {key}: {e}")
            return None
    
    def close(self) -> None:
        """关闭Redis连接"""
        try:
            if self._redis:
                self._redis.close()
                self._redis = None
                
            if self._pool:
                self._pool.disconnect()
                self._pool = None
                
            logger.info("Redis connection closed")
            
        except Exception as e:
            logger.error(f"Failed to close Redis connection: {e}")
            raise 