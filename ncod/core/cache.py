"""缓存模块"""

# 标准库导入
from datetime import datetime, timedelta
import json
from typing import Any, Dict, Optional, Union

# 第三方库导入
import redis
from prometheus_client import Counter, Histogram

# 本地导入
from ncod.core.config import settings
from ncod.core.log import get_logger

logger = get_logger(__name__)


class Cache:
    """缓存类"""

    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            socket_timeout=settings.REDIS_TIMEOUT,
            socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
            decode_responses=True,  # 自动解码响应
        )

        self._stats = {"hits": 0, "misses": 0, "hit_ratio": 0.0}

        self.metrics = {
            "cache_hits": Counter("cache_hits_total", "缓存命中次数"),
            "cache_misses": Counter("cache_misses_total", "缓存未命中次数"),
            "cache_operation_time": Histogram(
                "cache_operation_seconds",
                "缓存操作耗时",
                buckets=(0.001, 0.005, 0.01, 0.05, 0.1),
            ),
        }

    async def get(self, key: str) -> Optional[Dict]:
        """获取缓存"""
        try:
            with self.metrics["cache_operation_time"].time():
                value = self.client.get(key)
                if value:
                    self._stats["hits"] += 1
                    self.metrics["cache_hits"].inc()
                    try:
                        return json.loads(str(value))
                    except json.JSONDecodeError:
                        logger.error(f"缓存值解析失败: {value}")
                        return None
                self._stats["misses"] += 1
                self.metrics["cache_misses"].inc()
                return None
        except Exception as e:
            logger.error(f"获取缓存失败: {str(e)}")
            return None

    async def set(self, key: str, value: Dict, expire: int = 3600) -> bool:
        """设置缓存"""
        try:
            with self.metrics["cache_operation_time"].time():
                json_value = json.dumps(value)
                return bool(self.client.setex(key, expire, json_value))
        except Exception as e:
            logger.error(f"设置缓存失败: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            with self.metrics["cache_operation_time"].time():
                return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"删除缓存失败: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """获取缓存统计信息"""
        total = self._stats["hits"] + self._stats["misses"]
        if total > 0:
            self._stats["hit_ratio"] = self._stats["hits"] / total
        return self._stats
