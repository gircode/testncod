"""
API函数包
"""

from .devices import (
    get_device_alerts,
    get_device_metrics,
    get_device_status,
    get_device_trends,
)

__all__ = [
    "get_device_metrics",
    "get_device_status",
    "get_device_alerts",
    "get_device_trends",
]
