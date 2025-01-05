"""
Metrics Collector Module
"""

import asyncio
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Optional

from .metrics import (
    API_REQUEST_DURATION,
    API_REQUEST_SIZE,
    API_RESPONSE_SIZE,
    AUTH_FAILURES,
    CACHE_HIT_COUNT,
    CACHE_MISS_COUNT,
    CACHE_SIZE,
    DB_CONNECTION_POOL,
    DB_QUERY_DURATION,
    DB_TRANSACTION_COUNT,
    NODE_LATENCY,
    NODE_STATUS,
    RATE_LIMIT_HITS,
    SYNC_COUNT,
    SYNC_DATA_SIZE,
    SYNC_DURATION,
    SYSTEM_CPU,
    SYSTEM_MEMORY,
    TASK_COUNT,
    TASK_DURATION,
    TASK_QUEUE_SIZE,
)


class MetricsCollector:
    """Helper class for collecting and updating metrics"""

    @staticmethod
    def track_request_duration(
        method: str, endpoint: str, status: int, duration: float
    ):
        """Track API request duration"""
        API_REQUEST_DURATION.labels(
            method=method, endpoint=endpoint, status=status
        ).observe(duration)

    @staticmethod
    def track_request_size(method: str, endpoint: str, size: int):
        """Track API request size"""
        API_REQUEST_SIZE.labels(method=method, endpoint=endpoint).observe(size)

    @staticmethod
    def track_response_size(method: str, endpoint: str, size: int):
        """Track API response size"""
        API_RESPONSE_SIZE.labels(method=method, endpoint=endpoint).observe(size)

    @staticmethod
    def update_task_metrics(
        status: str, task_type: str, duration: Optional[float] = None
    ):
        """Update task-related metrics"""
        TASK_COUNT.labels(status=status).inc()
        if duration is not None:
            TASK_DURATION.labels(type=task_type).observe(duration)

    @staticmethod
    def update_queue_size(queue: str, size: int):
        """Update queue size metric"""
        TASK_QUEUE_SIZE.labels(queue=queue).set(size)

    @staticmethod
    def update_sync_metrics(
        status: str, sync_type: str, duration: float, data_size: int
    ):
        """Update synchronization metrics"""
        SYNC_COUNT.labels(status=status).inc()
        SYNC_DURATION.labels(type=sync_type).observe(duration)
        SYNC_DATA_SIZE.labels(type=sync_type).observe(data_size)

    @staticmethod
    def update_node_status(node_id: str, role: str, is_up: bool):
        """Update node status"""
        NODE_STATUS.labels(node_id=node_id, role=role).set(1 if is_up else 0)

    @staticmethod
    def track_node_latency(node_id: str, operation: str, latency: float):
        """Track node communication latency"""
        NODE_LATENCY.labels(node_id=node_id, operation=operation).observe(latency)

    @staticmethod
    def record_auth_failure(reason: str):
        """Record authentication failure"""
        AUTH_FAILURES.labels(reason=reason).inc()

    @staticmethod
    def record_rate_limit_hit(client_ip: str):
        """Record rate limit hit"""
        RATE_LIMIT_HITS.labels(client_ip=client_ip).inc()

    @staticmethod
    def update_db_metrics(pool_size: Dict[str, int], operation: str, duration: float):
        """Update database metrics"""
        for status, size in pool_size.items():
            DB_CONNECTION_POOL.labels(status=status).set(size)
        DB_QUERY_DURATION.labels(operation=operation).observe(duration)

    @staticmethod
    def record_db_transaction(status: str):
        """Record database transaction"""
        DB_TRANSACTION_COUNT.labels(status=status).inc()

    @staticmethod
    def update_cache_metrics(cache: str, hit: bool, size: Optional[int] = None):
        """Update cache metrics"""
        if hit:
            CACHE_HIT_COUNT.labels(cache=cache).inc()
        else:
            CACHE_MISS_COUNT.labels(cache=cache).inc()

        if size is not None:
            CACHE_SIZE.labels(cache=cache).set(size)

    @staticmethod
    @contextmanager
    def measure_time():
        """Context manager for measuring execution time"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            return duration

    @staticmethod
    def time_async_function(metric):
        """Decorator for measuring async function execution time"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    metric.observe(duration)

            return wrapper

        return decorator

    @staticmethod
    def time_function(metric):
        """Decorator for measuring function execution time"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    metric.observe(duration)

            return wrapper

        return decorator
