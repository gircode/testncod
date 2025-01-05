"""
Monitoring Configuration Module
"""

import os
from typing import Any, Dict, Optional

from pydantic import BaseSettings, Field


class MonitoringConfig(BaseSettings):
    """Configuration settings for monitoring"""

    # Prometheus settings
    prometheus_port: int = Field(default=9090, description="Port for Prometheus server")
    prometheus_path: str = Field(
        default="/metrics", description="Path for Prometheus metrics endpoint"
    )
    prometheus_pushgateway: Optional[str] = Field(
        default=None, description="Prometheus Pushgateway URL"
    )

    # Grafana settings
    grafana_port: int = Field(default=3000, description="Port for Grafana server")
    grafana_admin_password: str = Field(
        default="admin", description="Grafana admin password"
    )

    # Metrics collection settings
    collection_interval: int = Field(
        default=60, description="Interval in seconds for collecting system metrics"
    )

    request_duration_buckets: list = Field(
        default=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
        description="Buckets for request duration histogram",
    )

    request_size_buckets: list = Field(
        default=[100, 1000, 10000, 100000, 1000000],
        description="Buckets for request size histogram",
    )

    # Rate limiting settings
    rate_limit_window: int = Field(
        default=60, description="Window size in seconds for rate limiting"
    )

    rate_limit_max_requests: int = Field(
        default=100, description="Maximum number of requests per window"
    )

    # Node monitoring settings
    node_health_check_interval: int = Field(
        default=30, description="Interval in seconds for node health checks"
    )

    node_health_check_timeout: float = Field(
        default=5.0, description="Timeout in seconds for node health checks"
    )

    # Database monitoring settings
    db_slow_query_threshold: float = Field(
        default=1.0, description="Threshold in seconds for slow query logging"
    )

    db_connection_timeout: float = Field(
        default=5.0, description="Timeout in seconds for database connections"
    )

    # Cache monitoring settings
    cache_stats_interval: int = Field(
        default=300, description="Interval in seconds for cache statistics collection"
    )

    # Alert thresholds
    cpu_usage_threshold: float = Field(
        default=80.0, description="CPU usage threshold percentage for alerts"
    )

    memory_usage_threshold: float = Field(
        default=80.0, description="Memory usage threshold percentage for alerts"
    )

    disk_usage_threshold: float = Field(
        default=80.0, description="Disk usage threshold percentage for alerts"
    )

    # Logging settings
    log_metrics: bool = Field(
        default=True, description="Whether to log metrics to file"
    )

    log_file_path: str = Field(
        default="logs/metrics.log", description="Path to metrics log file"
    )

    log_rotation_interval: str = Field(
        default="1d", description="Log rotation interval"
    )

    # Export settings
    export_metrics: bool = Field(default=True, description="Whether to export metrics")

    export_interval: int = Field(
        default=60, description="Interval in seconds for metrics export"
    )

    export_format: str = Field(
        default="prometheus", description="Format for metrics export"
    )

    class Config:
        """Pydantic config"""

        env_prefix = "MONITORING_"
        case_sensitive = False

    def get_prometheus_config(self) -> Dict[str, Any]:
        """Get Prometheus configuration"""
        return {
            "port": self.prometheus_port,
            "path": self.prometheus_path,
            "pushgateway": self.prometheus_pushgateway,
        }

    def get_grafana_config(self) -> Dict[str, Any]:
        """Get Grafana configuration"""
        return {
            "port": self.grafana_port,
            "admin_password": self.grafana_admin_password,
        }

    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return {
            "window": self.rate_limit_window,
            "max_requests": self.rate_limit_max_requests,
        }

    def get_node_monitoring_config(self) -> Dict[str, Any]:
        """Get node monitoring configuration"""
        return {
            "health_check_interval": self.node_health_check_interval,
            "health_check_timeout": self.node_health_check_timeout,
        }

    def get_db_monitoring_config(self) -> Dict[str, Any]:
        """Get database monitoring configuration"""
        return {
            "slow_query_threshold": self.db_slow_query_threshold,
            "connection_timeout": self.db_connection_timeout,
        }

    def get_cache_monitoring_config(self) -> Dict[str, Any]:
        """Get cache monitoring configuration"""
        return {"stats_interval": self.cache_stats_interval}

    def get_alert_thresholds(self) -> Dict[str, float]:
        """Get alert thresholds"""
        return {
            "cpu_usage": self.cpu_usage_threshold,
            "memory_usage": self.memory_usage_threshold,
            "disk_usage": self.disk_usage_threshold,
        }

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "enabled": self.log_metrics,
            "file_path": self.log_file_path,
            "rotation_interval": self.log_rotation_interval,
        }

    def get_export_config(self) -> Dict[str, Any]:
        """Get export configuration"""
        return {
            "enabled": self.export_metrics,
            "interval": self.export_interval,
            "format": self.export_format,
        }
