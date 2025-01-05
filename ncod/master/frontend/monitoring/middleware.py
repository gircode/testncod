"""
Monitoring Middleware Module
"""

import os
import time
from typing import Callable

import psutil
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .metrics import (
    API_REQUEST_DURATION,
    API_REQUEST_SIZE,
    API_RESPONSE_SIZE,
    SYSTEM_CPU,
    SYSTEM_MEMORY,
)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting monitoring metrics"""

    def __init__(self, app: ASGIApp, system_metrics_interval: int = 60):
        super().__init__(app)
        self.system_metrics_interval = system_metrics_interval
        self.last_system_metrics_time = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Record request start time
        start_time = time.time()

        # Get request path template
        path_template = request.url.path
        for param in request.path_params:
            path_template = path_template.replace(
                str(request.path_params[param]), f"{{{param}}}"
            )

        # Record request size
        request_size = len(await request.body())
        API_REQUEST_SIZE.labels(method=request.method, endpoint=path_template).observe(
            request_size
        )

        try:
            # Call next middleware/endpoint
            response = await call_next(request)

            # Record response metrics
            duration = time.time() - start_time
            API_REQUEST_DURATION.labels(
                method=request.method,
                endpoint=path_template,
                status=response.status_code,
            ).observe(duration)

            # Record response size
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            response_size = len(response_body)
            API_RESPONSE_SIZE.labels(
                method=request.method, endpoint=path_template
            ).observe(response_size)

            # Create new response with captured body
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            API_REQUEST_DURATION.labels(
                method=request.method, endpoint=path_template, status=500
            ).observe(duration)
            raise e
        finally:
            # Update system metrics if interval has passed
            current_time = time.time()
            if (
                current_time - self.last_system_metrics_time
                >= self.system_metrics_interval
            ):
                self.update_system_metrics()
                self.last_system_metrics_time = current_time

    def update_system_metrics(self):
        """Update system metrics"""
        try:
            # CPU metrics
            cpu_times = psutil.cpu_times_percent()
            SYSTEM_CPU.labels(type="user").set(cpu_times.user)
            SYSTEM_CPU.labels(type="system").set(cpu_times.system)
            SYSTEM_CPU.labels(type="idle").set(cpu_times.idle)

            # Memory metrics
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY.labels(type="total").set(memory.total)
            SYSTEM_MEMORY.labels(type="available").set(memory.available)
            SYSTEM_MEMORY.labels(type="used").set(memory.used)
            SYSTEM_MEMORY.labels(type="free").set(memory.free)

            # Process metrics
            process = psutil.Process(os.getpid())
            SYSTEM_MEMORY.labels(type="process_rss").set(process.memory_info().rss)
            SYSTEM_MEMORY.labels(type="process_vms").set(process.memory_info().vms)
            SYSTEM_CPU.labels(type="process").set(process.cpu_percent())

        except Exception as e:
            # Log error but don't fail request
            import logging

            from ..config import settings

            logger = logging.getLogger(__name__)
            logger.error(f"Error updating system metrics: {e}")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting"""

    def __init__(
        self,
        app: ASGIApp,
        rate_limit: int = 100,  # requests per minute
        window_size: int = 60,  # seconds
    ):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_size = window_size
        self.requests = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host

        # Get current timestamp
        current_time = time.time()

        # Clean up old requests
        self.cleanup_old_requests(current_time)

        # Check rate limit
        if self.is_rate_limited(client_ip, current_time):
            return Response(content={"error": "Too many requests"}, status_code=429)

        # Record request
        self.record_request(client_ip, current_time)

        # Process request
        return await call_next(request)

    def cleanup_old_requests(self, current_time: float):
        """Clean up old requests"""
        cutoff_time = current_time - self.window_size
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                timestamp for timestamp in self.requests[ip] if timestamp > cutoff_time
            ]
            if not self.requests[ip]:
                del self.requests[ip]

    def is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client is rate limited"""
        if client_ip not in self.requests:
            return False

        # Count requests in current window
        cutoff_time = current_time - self.window_size
        recent_requests = len(
            [
                timestamp
                for timestamp in self.requests[client_ip]
                if timestamp > cutoff_time
            ]
        )

        return recent_requests >= self.rate_limit

    def record_request(self, client_ip: str, current_time: float):
        """Record a request"""
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
