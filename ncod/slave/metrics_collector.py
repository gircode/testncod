"""
指标采集模块
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

import aioredis
import psutil

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """指标值"""

    value: float
    timestamp: datetime
    labels: Dict = None


@dataclass
class Metric:
    """指标定义"""

    name: str
    type: str  # gauge, counter, histogram
    description: str
    unit: str = ""
    values: List[MetricValue] = None


class MetricsCollector:
    """指标采集器"""

    def __init__(self, redis_url: Optional[str] = None):
        self.metrics: Dict[str, Metric] = {}
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self._setup_default_metrics()

    def _setup_default_metrics(self):
        """设置默认指标"""
        self.add_metric(
            name="system_cpu_usage",
            type="gauge",
            description="System CPU usage percentage",
            unit="percent",
        )
        self.add_metric(
            name="system_memory_usage",
            type="gauge",
            description="System memory usage percentage",
            unit="percent",
        )
        self.add_metric(
            name="system_disk_usage",
            type="gauge",
            description="System disk usage percentage",
            unit="percent",
        )
        self.add_metric(
            name="system_network_io",
            type="counter",
            description="System network IO bytes",
            unit="bytes",
        )
        self.add_metric(
            name="device_status",
            type="gauge",
            description="Device online status",
            unit="",
        )
        self.add_metric(
            name="device_response_time",
            type="histogram",
            description="Device response time",
            unit="seconds",
        )

    def add_metric(self, name: str, type: str, description: str, unit: str = ""):
        """添加指标"""
        self.metrics[name] = Metric(
            name=name, type=type, description=description, unit=unit, values=[]
        )

    async def start(self):
        """启动指标采集"""
        if self.redis_url:
            self.redis = await aioredis.from_url(self.redis_url)
        asyncio.create_task(self._collect_system_metrics())

    async def stop(self):
        """停止指标采集"""
        if self.redis:
            await self.redis.close()

    async def _collect_system_metrics(self):
        """采集系统指标"""
        while True:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                await self.record_metric("system_cpu_usage", cpu_percent)

                # 内存使用率
                memory = psutil.virtual_memory()
                await self.record_metric("system_memory_usage", memory.percent)

                # 磁盘使用率
                disk = psutil.disk_usage("/")
                await self.record_metric("system_disk_usage", disk.percent)

                # 网络IO
                net_io = psutil.net_io_counters()
                await self.record_metric(
                    "system_network_io",
                    net_io.bytes_sent + net_io.bytes_recv,
                    labels={"direction": "total"},
                )

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")

            await asyncio.sleep(60)  # 每分钟采集一次

    async def record_metric(self, name: str, value: float, labels: Dict = None):
        """记录指标值"""
        if name not in self.metrics:
            logger.warning(f"Metric {name} not defined")
            return

        metric = self.metrics[name]
        metric_value = MetricValue(value=value, timestamp=datetime.now(), labels=labels)
        metric.values.append(metric_value)

        # 保留最近1000个数据点
        if len(metric.values) > 1000:
            metric.values = metric.values[-1000:]

        # 如果配置了Redis，同时保存到Redis
        if self.redis:
            try:
                await self._save_to_redis(name, metric_value)
            except Exception as e:
                logger.error(f"Error saving metric to Redis: {e}")

    async def _save_to_redis(self, name: str, value: MetricValue):
        """保存指标到Redis"""
        key = f"metrics:{name}"
        data = {
            "value": value.value,
            "timestamp": value.timestamp.isoformat(),
            "labels": value.labels,
        }
        await self.redis.lpush(key, json.dumps(data))
        await self.redis.ltrim(key, 0, 999)  # 保留最近1000个数据点

    def get_metric(self, name: str) -> Optional[Metric]:
        """获取指标"""
        return self.metrics.get(name)

    def get_all_metrics(self) -> Dict[str, Metric]:
        """获取所有指标"""
        return self.metrics

    async def get_metric_values(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[MetricValue]:
        """获取指标值"""
        metric = self.metrics.get(name)
        if not metric:
            return []

        values = metric.values
        if start_time:
            values = [v for v in values if v.timestamp >= start_time]
        if end_time:
            values = [v for v in values if v.timestamp <= end_time]
        return values

    async def export_metrics(self) -> Dict:
        """导出所有指标"""
        result = {}
        for name, metric in self.metrics.items():
            result[name] = {
                "type": metric.type,
                "description": metric.description,
                "unit": metric.unit,
                "values": [asdict(v) for v in metric.values],
            }
        return result

    async def import_metrics(self, data: Dict):
        """导入指标数据"""
        for name, metric_data in data.items():
            if name not in self.metrics:
                self.add_metric(
                    name=name,
                    type=metric_data["type"],
                    description=metric_data["description"],
                    unit=metric_data["unit"],
                )
            metric = self.metrics[name]
            metric.values = [MetricValue(**v) for v in metric_data["values"]]

    def clear_metrics(self, name: Optional[str] = None):
        """清除指标数据"""
        if name:
            if name in self.metrics:
                self.metrics[name].values = []
        else:
            for metric in self.metrics.values():
                metric.values = []

    async def calculate_statistics(self, name: str) -> Dict:
        """计算指标统计信息"""
        values = await self.get_metric_values(name)
        if not values:
            return {}

        raw_values = [v.value for v in values]
        return {
            "count": len(raw_values),
            "min": min(raw_values),
            "max": max(raw_values),
            "avg": sum(raw_values) / len(raw_values),
            "last": raw_values[-1],
        }
