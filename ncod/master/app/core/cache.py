"""
缓存模块
"""

from typing import Any, Dict, Optional, cast

import aioredis
from aioredis import Redis
from app.core.config import settings
from app.core.errors import ErrorHandler


class CacheManager:
    """缓存管理器"""

    def __init__(self, error_handler: ErrorHandler):
        """初始化缓存管理器

        Args:
            error_handler: 错误处理器
        """
        self.error_handler = error_handler
        self.redis_client: Optional[Redis] = None
        self.status: str = "inactive"
        self.headers: Dict[str, Any] = {}
        self.body: Dict[str, Any] = {}

    async def connect(self) -> None:
        """连接Redis服务器"""
        try:
            self.redis_client = await aioredis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB \
                    }",
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            await self.redis_client.ping()
            self.status = "active"
        except Exception as e:
            self.error_handler.handle_error(e)
            raise

    async def disconnect(self) -> None:
        """断开Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            self.status = "inactive"

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """设置缓存

        Args:
            key: 键
            value: 值
            expire: 过期时间(秒)
        """
        if not self.redis_client:
            await self.connect()
        try:
            client = cast(Redis, self.redis_client)
            await client.set(
                f"{settings.CACHE_KEY_PREFIX}{key}",
                value,
                ex=expire or settings.CACHE_DEFAULT_TIMEOUT,
            )
        except Exception as e:
            self.error_handler.handle_error(e)
            raise

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存

        Args:
            key: 键

        Returns:
            缓存值
        """
        if not self.redis_client:
            await self.connect()
        try:
            client = cast(Redis, self.redis_client)
            return await client.get(f"{settings.CACHE_KEY_PREFIX}{key}")
        except Exception as e:
            self.error_handler.handle_error(e)
            raise

    async def delete(self, key: str) -> None:
        """删除缓存

        Args:
            key: 键
        """
        if not self.redis_client:
            await self.connect()
        try:
            client = cast(Redis, self.redis_client)
            await client.delete(f"{settings.CACHE_KEY_PREFIX}{key}")
        except Exception as e:
            self.error_handler.handle_error(e)
            raise

    async def clear(self) -> None:
        """清空缓存"""
        if not self.redis_client:
            await self.connect()
        try:
            client = cast(Redis, self.redis_client)
            await client.flushdb()
        except Exception as e:
            self.error_handler.handle_error(e)
            raise


# ... 其余代码保持不变 ...
