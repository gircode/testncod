"""
Performance Monitoring Module
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List

import psutil


class PerformanceMonitor:
    """系统性能监控工具"""

    def __init__(self):
        self.history_size = 100  # 保留最近100个数据点
        self.cpu_history: List[Dict[str, Any]] = []
        self.memory_history: List[Dict[str, Any]] = []
        self.io_history: List[Dict[str, Any]] = []

    def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        return psutil.cpu_percent(interval=1)

    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        mem = psutil.virtual_memory()
        return {
            "total": mem.total / (1024 * 1024 * 1024),  # GB
            "used": mem.used / (1024 * 1024 * 1024),  # GB
            "percent": mem.percent,
        }

    def get_disk_usage(self) -> Dict[str, float]:
        """获取磁盘使用情况"""
        disk = psutil.disk_usage("/")
        return {
            "total": disk.total / (1024 * 1024 * 1024),  # GB
            "used": disk.used / (1024 * 1024 * 1024),  # GB
            "percent": disk.percent,
        }

    def get_network_io(self) -> Dict[str, float]:
        """获取网络IO情况"""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent / (1024 * 1024),  # MB
            "bytes_recv": net_io.bytes_recv / (1024 * 1024),  # MB
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
        }

    def update_history(self) -> None:
        """更新历史数据"""
        timestamp = datetime.now().isoformat()

        # CPU历史
        cpu_data = {"timestamp": timestamp, "value": self.get_cpu_usage()}
        self.cpu_history.append(cpu_data)
        if len(self.cpu_history) > self.history_size:
            self.cpu_history.pop(0)

        # 内存历史
        memory_data = {
            "timestamp": timestamp,
            "value": self.get_memory_usage()["percent"],
        }
        self.memory_history.append(memory_data)
        if len(self.memory_history) > self.history_size:
            self.memory_history.pop(0)

        # IO历史
        io_data = {"timestamp": timestamp, "value": self.get_network_io()}
        self.io_history.append(io_data)
        if len(self.io_history) > self.history_size:
            self.io_history.pop(0)

    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标汇总"""
        return {
            "cpu": {"current": self.get_cpu_usage(), "history": self.cpu_history},
            "memory": {
                "current": self.get_memory_usage(),
                "history": self.memory_history,
            },
            "disk": self.get_disk_usage(),
            "network": {"current": self.get_network_io(), "history": self.io_history},
        }

    async def monitor_async(self, interval: int = 5) -> None:
        """异步监控系统性能"""
        while True:
            self.update_history()
            await asyncio.sleep(interval)


# 创建全局性能监控实例
performance_monitor = PerformanceMonitor()


def performance_metric(metric_value: Any) -> Any:
    """性能指标处理函数

    Args:
        metric_value: 任意类型的性能指标值
    Returns:
        处理后的性能指标值
    """
    return metric_value
