"""系统监控模块"""

import psutil
from datetime import datetime
from typing import Dict, Any


class SystemMonitor:
    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """获取系统状态统计"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def get_process_stats() -> Dict[str, Any]:
        """获取进程状态统计"""
        process = psutil.Process()
        return {
            "cpu_percent": process.cpu_percent(interval=1),
            "memory_percent": process.memory_percent(),
            "threads": process.num_threads(),
            "connections": len(process.connections()),
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def check_database_health(db) -> bool:
        """检查数据库健康状态"""
        try:
            await db.execute("SELECT 1")
            return True
        except Exception:
            return False
