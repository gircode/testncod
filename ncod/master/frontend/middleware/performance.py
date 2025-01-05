"""
Performance Middleware Module
"""

import gzip
import re
import time
from typing import Dict, List

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class PerformanceMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, app, min_compression_size: int = 1000, exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.min_compression_size = min_compression_size
        self.exclude_paths = exclude_paths or []

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        response.headers["X-Process-Time"] = str(process_time)
        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, cache_control_rules: Dict[str, str]):
        super().__init__(app)
        self.cache_control_rules = cache_control_rules

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        content_type = response.headers.get("content-type", "")

        for content_pattern, cache_rule in self.cache_control_rules.items():
            if re.search(content_pattern, content_type, re.IGNORECASE):
                response.headers["Cache-Control"] = cache_rule
                break

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response
