"""
Monitoring Settings Module
"""

import os
from datetime import timedelta
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseSettings, Field, validator


class PrometheusSettings(BaseSettings):
    """Prometheus configuration settings"""

    host: str = Field(default="localhost", description="Prometheus server host")
    port: int = Field(default=9090, description="Prometheus server port")
    metrics_path: str = Field(default="/metrics", description="Metrics endpoint path")
    scrape_interval: int = Field(default=15, description="Scrape interval in seconds")
    evaluation_interval: int = Field(
        default=15, description="Evaluation interval in seconds"
    )
    retention_time: str = Field(default="15d", description="Data retention period")
    storage_path: str = Field(
        default="data/prometheus", description="Data storage path"
    )
    external_labels: Dict[str, str] = Field(
        default_factory=dict, description="External labels to add to metrics"
    )

    class Config:
        env_prefix = "PROMETHEUS_"


class GrafanaSettings(BaseSettings):
    """Grafana configuration settings"""

    host: str = Field(default="localhost", description="Grafana server host")
    port: int = Field(default=3000, description="Grafana server port")
    admin_user: str = Field(default="admin", description="Admin username")
    admin_password: str = Field(default="admin", description="Admin password")
    secret_key: str = Field(
        default="your-secret-key", description="Secret key for sessions"
    )
    install_plugins: List[str] = Field(
        default_factory=list, description="Plugins to install"
    )
    allow_embedding: bool = Field(
        default=False, description="Allow dashboard embedding"
    )
    auth_anonymous: bool = Field(default=False, description="Enable anonymous access")

    class Config:
        env_prefix = "GRAFANA_"


class AlertManagerSettings(BaseSettings):
    """Alert Manager configuration settings"""

    host: str = Field(default="localhost", description="Alert Manager host")
    port: int = Field(default=9093, description="Alert Manager port")
    resolve_timeout: str = Field(default="5m", description="Alert resolution timeout")
    smtp_host: Optional[str] = Field(default=None, description="SMTP server host")
    smtp_port: Optional[int] = Field(default=None, description="SMTP server port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    slack_api_url: Optional[str] = Field(default=None, description="Slack webhook URL")
    slack_channel: Optional[str] = Field(default=None, description="Slack channel")

    class Config:
        env_prefix = "ALERTMANAGER_"


class MetricsSettings(BaseSettings):
    """Metrics collection settings"""

    enabled_metrics: List[str] = Field(
        default=["system", "api", "database", "cache", "task", "node"],
        description="Enabled metric collectors",
    )
    collection_interval: int = Field(
        default=60, description="Collection interval in seconds"
    )
    retention_days: int = Field(default=30, description="Data retention period in days")
    batch_size: int = Field(default=1000, description="Batch size for metric storage")
    storage_path: str = Field(
        default="data/metrics", description="Metrics storage path"
    )

    class Config:
        env_prefix = "METRICS_"


class LoggingSettings(BaseSettings):
    """Logging configuration settings"""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )
    file_path: str = Field(default="logs/monitoring.log", description="Log file path")
    max_size: int = Field(default=10485760, description="Maximum log file size")  # 10MB
    backup_count: int = Field(default=5, description="Number of backup files")
    json_format: bool = Field(default=True, description="Use JSON format for logs")

    class Config:
        env_prefix = "LOGGING_"


class AlertSettings(BaseSettings):
    """Alert configuration settings"""

    enabled: bool = Field(default=True, description="Enable alerting")
    check_interval: int = Field(
        default=60, description="Alert check interval in seconds"
    )
    thresholds: Dict[str, float] = Field(
        default={
            "cpu_usage": 80.0,
            "memory_usage": 80.0,
            "disk_usage": 80.0,
            "error_rate": 5.0,
            "response_time": 1.0,
        },
        description="Alert thresholds",
    )
    notification_channels: List[str] = Field(
        default=["email"], description="Enabled notification channels"
    )

    class Config:
        env_prefix = "ALERT_"


class MonitoringSettings(BaseSettings):
    """Main monitoring configuration settings"""

    environment: str = Field(default="development", description="Environment name")
    base_dir: str = Field(default=".", description="Base directory for monitoring")
    prometheus: PrometheusSettings = Field(
        default_factory=PrometheusSettings, description="Prometheus settings"
    )
    grafana: GrafanaSettings = Field(
        default_factory=GrafanaSettings, description="Grafana settings"
    )
    alertmanager: AlertManagerSettings = Field(
        default_factory=AlertManagerSettings, description="Alert Manager settings"
    )
    metrics: MetricsSettings = Field(
        default_factory=MetricsSettings, description="Metrics settings"
    )
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings, description="Logging settings"
    )
    alerts: AlertSettings = Field(
        default_factory=AlertSettings, description="Alert settings"
    )

    class Config:
        env_prefix = "MONITORING_"

    @validator("base_dir")
    def validate_base_dir(cls, v: str) -> str:
        """Validate and create base directory"""
        os.makedirs(v, exist_ok=True)
        return os.path.abspath(v)

    def save_config(self, config_path: str):
        """Save configuration to file"""
        config_dir = os.path.dirname(config_path)
        os.makedirs(config_dir, exist_ok=True)

        config = {
            "environment": self.environment,
            "base_dir": self.base_dir,
            "prometheus": self.prometheus.dict(),
            "grafana": self.grafana.dict(),
            "alertmanager": self.alertmanager.dict(),
            "metrics": self.metrics.dict(),
            "logging": self.logging.dict(),
            "alerts": self.alerts.dict(),
        }

        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    @classmethod
    def load_config(cls, config_path: str) -> "MonitoringSettings":
        """Load configuration from file"""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return cls(**config)

    def get_data_dir(self) -> str:
        """Get data directory path"""
        data_dir = os.path.join(self.base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

    def get_log_dir(self) -> str:
        """Get log directory path"""
        log_dir = os.path.dirname(self.logging.file_path)
        os.makedirs(log_dir, exist_ok=True)
        return log_dir

    def get_metrics_dir(self) -> str:
        """Get metrics directory path"""
        metrics_dir = os.path.join(self.base_dir, self.metrics.storage_path)
        os.makedirs(metrics_dir, exist_ok=True)
        return metrics_dir

    def get_prometheus_dir(self) -> str:
        """Get Prometheus data directory path"""
        prometheus_dir = os.path.join(self.base_dir, self.prometheus.storage_path)
        os.makedirs(prometheus_dir, exist_ok=True)
        return prometheus_dir

    def get_retention_delta(self) -> timedelta:
        """Get retention period as timedelta"""
        return timedelta(days=self.metrics.retention_days)

    def get_collection_interval(self) -> timedelta:
        """Get collection interval as timedelta"""
        return timedelta(seconds=self.metrics.collection_interval)

    def get_alert_interval(self) -> timedelta:
        """Get alert check interval as timedelta"""
        return timedelta(seconds=self.alerts.check_interval)
