"""
NCOD从服务器包
"""

from .app import App, run
from .config import Config, load_config
from .device_manager import DeviceConfig, DeviceManager, DeviceStatus
from .metrics_collector import Metric, MetricsCollector, MetricValue

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "App",
    "run",
    "Config",
    "load_config",
    "DeviceManager",
    "DeviceConfig",
    "DeviceStatus",
    "MetricsCollector",
    "Metric",
    "MetricValue",
]

# 版本信息
VERSION = (0, 1, 0)
VERSION_INFO = ".".join(str(c) for c in VERSION)
VERSION_STRING = f"NCOD Slave Server {VERSION_INFO}"

# 包元数据
PACKAGE_NAME = "ncod-slave"
PACKAGE_DESCRIPTION = "NCOD从服务器 - 设备管理和监控服务"
PACKAGE_URL = "https://github.com/yourusername/ncod"
PACKAGE_LICENSE = "MIT"

# 默认配置
DEFAULT_CONFIG_PATH = "config/slave.json"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = "INFO"

# API版本
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# 状态码
STATUS_OK = "ok"
STATUS_ERROR = "error"
STATUS_UNKNOWN = "unknown"
