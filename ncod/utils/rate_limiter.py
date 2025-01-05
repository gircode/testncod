"""API速率限制模块"""

import time
from datetime import datetime
from typing import Dict, Optional, Tuple, cast
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from ncod.utils.logger import logger
from ncod.utils.cache import redis_cache
from ncod.utils.config import settings


class RateLimiter(BaseHTTPMiddleware):
    """API速率限制中间件"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理器

        Returns:
            Response: 响应对象

        Raises:
            HTTPException: 请求超过限制时抛出429错误
        """
        try:
            # 获取客户端标识
            client_id = self._get_client_id(request)

            # 检查速率限制
            allowed, headers = await self._check_rate_limit(client_id)
            if not allowed:
                raise HTTPException(status_code=429, detail="请求过于频繁,请稍后再试")

            # 处理请求
            response = await call_next(request)

            # 添加速率限制响应头
            for key, value in headers.items():
                response.headers[key] = str(value)

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"速率限制检查失败: {e}")
            return await call_next(request)

    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识

        Args:
            request: 请求对象

        Returns:
            str: 客户端标识
        """
        # 优先使用API密钥
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api:{api_key}"

        # 其次使用认证令牌
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            return f"token:{auth[7:]}"

        # 最后使用IP地址
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        client = request.client
        if client and client.host:
            return f"ip:{client.host}"

        return "ip:unknown"

    async def _check_rate_limit(self, client_id: str) -> Tuple[bool, Dict[str, str]]:
        """检查速率限制

        Args:
            client_id: 客户端标识

        Returns:
            Tuple[bool, Dict[str, str]]: (是否允许请求, 响应头)
        """
        try:
            # 获取客户端配置
            config = await self._get_client_config(client_id)

            # 获取当前时间窗口
            window = int(time.time() / config["period"]) * config["period"]

            # 构造缓存键
            cache_key = f"rate_limit:{client_id}:{window}"

            # 获取当前请求计数
            count = await redis_cache.get(cache_key)
            if count is None:
                count = 0

            # 检查是否超过限制
            allowed = count < config["limit"]

            # 更新请求计数
            if allowed:
                await redis_cache.set(cache_key, count + 1, expire=config["period"])

            # 计算剩余配额
            remaining = max(0, config["limit"] - (count + 1))

            # 计算重置时间
            reset = window + config["period"]

            # 构造响应头
            headers = {
                "X-RateLimit-Limit": str(config["limit"]),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset),
            }

            if not allowed:
                retry_after = reset - int(time.time())
                headers["Retry-After"] = str(retry_after)

            return allowed, headers

        except Exception as e:
            logger.error(f"检查速率限制失败: {e}")
            return True, {}

    async def _get_client_config(self, client_id: str) -> Dict:
        """获取客户端配置

        Args:
            client_id: 客户端标识

        Returns:
            Dict: 客户端配置
        """
        try:
            # 从缓存获取配置
            cache_key = f"rate_limit_config:{client_id}"
            config = await redis_cache.get(cache_key)

            if config:
                return config

            # 获取默认配置
            config = {
                "limit": settings.RATE_LIMIT_REQUESTS,
                "period": settings.RATE_LIMIT_PERIOD,
            }

            # 根据客户端类型调整配置
            client_type = client_id.split(":", 1)[0]

            if client_type == "api":
                # API密钥客户端
                config["limit"] = int(config["limit"] * 2)  # 更高的限制
            elif client_type == "token":
                # 认证令牌客户端
                config["limit"] = int(config["limit"] * 1.5)  # 较高的限制

            # 缓存配置
            await redis_cache.set(
                cache_key, config, expire=settings.RATE_LIMIT_CONFIG_TTL
            )

            return config

        except Exception as e:
            logger.error(f"获取客户端配置失败: {e}")
            return {
                "limit": settings.RATE_LIMIT_REQUESTS,
                "period": settings.RATE_LIMIT_PERIOD,
            }

    async def get_client_usage(self, client_id: str) -> Optional[Dict]:
        """获取客户端使用情况

        Args:
            client_id: 客户端标识

        Returns:
            Optional[Dict]: 使用情况
        """
        try:
            # 获取客户端配置
            config = await self._get_client_config(client_id)

            # 获取当前时间窗口
            window = int(time.time() / config["period"]) * config["period"]

            # 获取当前请求计数
            cache_key = f"rate_limit:{client_id}:{window}"
            count = await redis_cache.get(cache_key)

            if count is None:
                return None

            return {
                "client_id": client_id,
                "limit": config["limit"],
                "used": count,
                "remaining": max(0, config["limit"] - count),
                "reset_time": datetime.fromtimestamp(
                    window + config["period"]
                ).isoformat(),
            }

        except Exception as e:
            logger.error(f"获取客户端使用情况失败: {e}")
            return None

    async def reset_client_limit(self, client_id: str) -> bool:
        """重置客户端限制

        Args:
            client_id: 客户端标识

        Returns:
            bool: 是否重置成功
        """
        try:
            # 获取客户端配置
            config = await self._get_client_config(client_id)

            # 获取当前时间窗口
            window = int(time.time() / config["period"]) * config["period"]

            # 删除请求计数
            cache_key = f"rate_limit:{client_id}:{window}"
            await redis_cache.delete(cache_key)

            return True

        except Exception as e:
            logger.error(f"重置客户端限制失败: {e}")
            return False

    async def update_client_config(
        self, client_id: str, limit: Optional[int] = None, period: Optional[int] = None
    ) -> bool:
        """更新客户端配置

        Args:
            client_id: 客户端标识
            limit: 请求限制
            period: 时间周期(秒)

        Returns:
            bool: 是否更新成功
        """
        try:
            # 获取当前配置
            config = await self._get_client_config(client_id)

            # 更新配置
            if limit is not None:
                config["limit"] = limit
            if period is not None:
                config["period"] = period

            # 缓存配置
            cache_key = f"rate_limit_config:{client_id}"
            await redis_cache.set(
                cache_key, config, expire=settings.RATE_LIMIT_CONFIG_TTL
            )

            return True

        except Exception as e:
            logger.error(f"更新客户端配置失败: {e}")
            return False


# 创建全局速率限制器实例
rate_limiter = RateLimiter
