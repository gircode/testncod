from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel
import enum


class TimeRange(str, enum.Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class DeviceMetric(BaseModel):
    timestamp: datetime
    is_connected: bool
    usage_duration: float
    bandwidth_usage: float
    error_count: int


class DeviceMetricsResponse(BaseModel):
    device_id: int
    time_range: TimeRange
    metrics: List[DeviceMetric]


class SlaveMetric(BaseModel):
    timestamp: datetime
    is_healthy: bool
    device_count: int
    cpu_usage: float
    memory_usage: float
    network_tx: float
    network_rx: float


class SlaveMetricsResponse(BaseModel):
    slave_id: int
    time_range: TimeRange
    metrics: List[SlaveMetric]


class SystemMetricsResponse(BaseModel):
    total_slaves: int
    healthy_slaves: int
    total_devices: int
    connected_devices: int
    slave_metrics: List[Dict[str, Any]]
    device_metrics: List[Dict[str, Any]]
    timestamp: str


class MetricsCollectionConfig(BaseModel):
    metrics_collection_interval: int = 60
    metrics_retention_days: int = 30
