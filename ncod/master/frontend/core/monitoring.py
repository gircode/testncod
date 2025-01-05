"""
监控工具类
"""

import time
from typing import Any, Dict

import psutil
from prometheus_client import Counter, Gauge, Histogram

# 性能指标
REQUEST_COUNT = Counter(
    "frontend_request_total",
    "Total number of frontend requests",
    ["method", "endpoint"],
)

ERROR_COUNT = Counter(
    "frontend_error_total", "Total number of frontend errors", ["type"]
)

REQUEST_LATENCY = Histogram(
    "frontend_request_latency_seconds",
    "Frontend request latency in seconds",
    ["method", "endpoint"],
)

MEMORY_USAGE = Gauge("frontend_memory_usage_bytes", "Frontend memory usage in bytes")

CPU_USAGE = Gauge("frontend_cpu_usage_percent", "Frontend CPU usage percentage")


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0
        self._total_latency = 0.0

    def record_request(self, method: str, endpoint: str, latency: float) -> None:
        """记录请求"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)

        self._request_count += 1
        self._total_latency += latency

    def record_error(self, error_type: str = "unknown") -> None:
        """记录错误"""
        ERROR_COUNT.labels(type=error_type).inc()
        self._error_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        # 更新系统指标
        memory = psutil.Process().memory_info()
        MEMORY_USAGE.set(memory.rss)

        cpu_percent = psutil.Process().cpu_percent()
        CPU_USAGE.set(cpu_percent)

        # 计算平均响应时间
        avg_response_time = (
            self._total_latency / self._request_count
            if self._request_count > 0
            else 0.0
        )

        return {
            "uptime": time.time() - self._start_time,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "avg_response_time": avg_response_time * 1000,  # 转换为毫秒
            "memory_usage": memory.rss,
            "cpu_usage": cpu_percent,
        }
