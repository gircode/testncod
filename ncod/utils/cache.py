"""缓存模块"""

import json
from typing import Any, Dict, Optional, Union, cast, Callable, Awaitable
import aioredis
from aioredis.client import Redis, PubSub

from ncod.utils.config import settings
from ncod.utils.logger import logger


class RedisCache:
    """Redis缓存管理器"""

    def __init__(self):
        self._redis: Optional[Redis] = None
        self._pubsub: Optional[PubSub] = None

    async def init(self):
        """初始化Redis连接"""
        try:
            if not self._redis:
                self._redis = await aioredis.from_url(settings.REDIS_URL)
                logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise

    async def close(self):
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis连接已关闭")

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            Any: 缓存值,不存在则返回None
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            value = await redis.get(key)
            if value:
                return json.loads(value)
            return None

        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间(秒)

        Returns:
            bool: 是否设置成功
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            value_str = json.dumps(value)
            if expire:
                await redis.setex(key, expire, value_str)
            else:
                await redis.set(key, value_str)
            return True

        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存

        Args:
            key: 缓存键

        Returns:
            bool: 是否删除成功
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            await redis.delete(key)
            return True

        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            bool: 是否存在
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            return await redis.exists(key) > 0

        except Exception as e:
            logger.error(f"检查缓存是否存在失败: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """获取缓存剩余过期时间

        Args:
            key: 缓存键

        Returns:
            int: 剩余过期时间(秒),-1表示永不过期,-2表示不存在
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            return await redis.ttl(key)

        except Exception as e:
            logger.error(f"获取缓存过期时间失败: {e}")
            return -2

    async def incr(self, key: str, amount: int = 1) -> int:
        """递增缓存值

        Args:
            key: 缓存键
            amount: 递增量

        Returns:
            int: 递增后的值
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            return await redis.incrby(key, amount)

        except Exception as e:
            logger.error(f"递增缓存值失败: {e}")
            return 0

    async def decr(self, key: str, amount: int = 1) -> int:
        """递减缓存值

        Args:
            key: 缓存键
            amount: 递减量

        Returns:
            int: 递减后的值
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            return await redis.decrby(key, amount)

        except Exception as e:
            logger.error(f"递减缓存值失败: {e}")
            return 0

    async def keys(self, pattern: str = "*") -> list[str]:
        """获取匹配的缓存键列表

        Args:
            pattern: 匹配模式

        Returns:
            list[str]: 匹配的键列表
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            keys = await redis.keys(pattern)
            return [key.decode() for key in keys]

        except Exception as e:
            logger.error(f"获取缓存键列表失败: {e}")
            return []

    async def flush(self) -> bool:
        """清空所有缓存

        Returns:
            bool: 是否清空成功
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            await redis.flushdb()
            return True

        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return False

    async def get_info(self) -> Dict[str, Any]:
        """获取Redis信息

        Returns:
            Dict[str, Any]: Redis信息
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            info = await redis.info()
            return {
                key.decode(): value.decode() if isinstance(value, bytes) else value
                for key, value in info.items()
            }

        except Exception as e:
            logger.error(f"获取Redis信息失败: {e}")
            return {}

    async def publish(self, channel: str, message: Any) -> int:
        """发布消息

        Args:
            channel: 频道名称
            message: 消息内容

        Returns:
            int: 接收到消息的客户端数量
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            message_str = (
                json.dumps(message)
                if not isinstance(message, (str, bytes))
                else message
            )
            return await redis.publish(channel, message_str)

        except Exception as e:
            logger.error(f"发布消息失败: {e}")
            return 0

    async def subscribe(
        self, channel: str, callback: Callable[[str, Any], Awaitable[None]]
    ):
        """订阅频道

        Args:
            channel: 频道名称
            callback: 回调函数,接收频道名称和消息内容作为参数
        """
        try:
            if not self._redis:
                await self.init()

            redis = cast(Redis, self._redis)
            if not self._pubsub:
                self._pubsub = redis.pubsub()

            pubsub = cast(PubSub, self._pubsub)
            await pubsub.subscribe(channel)

            while True:
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    if message:
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode()
                        if not isinstance(data, str):
                            data = json.dumps(data)

                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            pass

                        await callback(channel, data)

                except Exception as e:
                    logger.error(f"处理订阅消息失败: {e}")

        except Exception as e:
            logger.error(f"订阅频道失败: {e}")

    async def unsubscribe(self, channel: str):
        """取消订阅频道

        Args:
            channel: 频道名称
        """
        try:
            if self._pubsub:
                pubsub = cast(PubSub, self._pubsub)
                await pubsub.unsubscribe(channel)

        except Exception as e:
            logger.error(f"取消订阅频道失败: {e}")

    async def close_pubsub(self):
        """关闭发布/订阅连接"""
        try:
            if self._pubsub:
                pubsub = cast(PubSub, self._pubsub)
                await pubsub.close()
                self._pubsub = None

        except Exception as e:
            logger.error(f"关闭发布/订阅连接失败: {e}")


# 创建全局缓存实例
redis_cache = RedisCache()
