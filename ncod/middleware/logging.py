"""日志中间件"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..utils.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        start_time = time.time()

        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录请求日志
        logger.info(
            "Request processed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host,
                "process_time": f"{process_time:.3f}s",
                "status_code": response.status_code,
            },
        )

        return response
