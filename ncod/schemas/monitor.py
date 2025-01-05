"""监控相关的Pydantic模型"""

from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel


class SystemStats(BaseModel):
    """系统状态模型"""

    cpu_percent: float
    memory_percent: float
    disk_usage: float
    disk_free: int
    network_io: Dict[str, int]
    timestamp: datetime


class ProcessStats(BaseModel):
    """进程状态模型"""

    cpu_percent: float
    memory_percent: float
    threads: int
    timestamp: datetime
