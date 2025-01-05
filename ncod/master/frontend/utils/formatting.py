"""
格式化工具函数
"""

from datetime import timedelta
from typing import Union


def format_bytes(size: Union[int, float]) -> str:
    """格式化字节大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_duration(seconds: Union[int, float, timedelta]) -> str:
    """格式化时间间隔"""
    if isinstance(seconds, timedelta):
        seconds = seconds.total_seconds()

    units = [
        ("年", 365 * 24 * 60 * 60),
        ("月", 30 * 24 * 60 * 60),
        ("天", 24 * 60 * 60),
        ("小时", 60 * 60),
        ("分钟", 60),
        ("秒", 1),
    ]

    if seconds < 1:
        return "刚刚"

    for unit, div in units:
        if seconds >= div:
            value = int(seconds / div)
            return f"{value}{unit}"

    return "刚刚"


def format_number(num: Union[int, float]) -> str:
    """格式化数字"""
    if isinstance(num, float):
        return f"{num:.2f}"
    return str(num)
