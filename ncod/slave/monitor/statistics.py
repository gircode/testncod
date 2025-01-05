"""设备统计系统"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.slave.device.manager import device_manager

logger = setup_logger("statistics")


@dataclass
class DeviceStats:
    """设备统计信息"""

    device_id: str
    total_usage_time: int  # 总使用时间(秒)
    session_count: int  # 会话数量
    error_count: int  # 错误次数
    avg_session_time: float  # 平均会话时长
    last_used: Optional[datetime]  # 最后使用时间
    status_history: List[Dict]  # 状态历史


@dataclass
class UserStats:
    """用户统计信息"""

    user_id: str
    total_usage_time: int
    device_count: int
    session_count: int
    last_active: Optional[datetime]


class StatisticsCollector:
    """统计收集器"""

    def __init__(self):
        self.running = False
        self.device_stats: Dict[str, DeviceStats] = {}
        self.user_stats: Dict[str, UserStats] = {}
        self.hourly_stats: Dict[str, Dict] = defaultdict(dict)
        self.daily_stats: Dict[str, Dict] = defaultdict(dict)

    async def start(self):
        """启动统计收集器"""
        try:
            self.running = True
            asyncio.create_task(self._stats_collection_loop())
            logger.info("Statistics collector started")
        except Exception as e:
            logger.error(f"Error starting statistics collector: {e}")
            raise

    async def stop(self):
        """停止统计收集器"""
        try:
            self.running = False
            logger.info("Statistics collector stopped")
        except Exception as e:
            logger.error(f"Error stopping statistics collector: {e}")

    async def _stats_collection_loop(self):
        """统计收集循环"""
        while self.running:
            try:
                await self._collect_current_stats()
                await self._aggregate_stats()
                await asyncio.sleep(config.stats_interval)
            except Exception as e:
                logger.error(f"Error in stats collection loop: {e}")
                await asyncio.sleep(5)

    async def _collect_current_stats(self):
        """收集当前统计"""
        try:
            devices = device_manager.controller.devices
            for device_id, device in devices.items():
                usage = device_manager.get_device_usage(device_id)
                if not usage:
                    continue

                # 更新设备统计
                if device_id not in self.device_stats:
                    self.device_stats[device_id] = DeviceStats(
                        device_id=device_id,
                        total_usage_time=0,
                        session_count=0,
                        error_count=0,
                        avg_session_time=0,
                        last_used=None,
                        status_history=[],
                    )

                stats = self.device_stats[device_id]
                current_session = usage.get("current_session")

                if current_session:
                    user_id = current_session["user_id"]
                    session_time = (
                        datetime.utcnow() - current_session["start_time"]
                    ).total_seconds()

                    # 更新设备统计
                    stats.total_usage_time += session_time
                    stats.session_count += 1
                    stats.last_used = datetime.utcnow()
                    stats.avg_session_time = (
                        stats.total_usage_time / stats.session_count
                    )

                    # 更新用户统计
                    if user_id not in self.user_stats:
                        self.user_stats[user_id] = UserStats(
                            user_id=user_id,
                            total_usage_time=0,
                            device_count=0,
                            session_count=0,
                            last_active=None,
                        )

                    user_stats = self.user_stats[user_id]
                    user_stats.total_usage_time += session_time
                    user_stats.device_count += 1
                    user_stats.session_count += 1
                    user_stats.last_active = datetime.utcnow()

                # 记录状态历史
                stats.status_history.append(
                    {"status": device["status"], "timestamp": datetime.utcnow()}
                )

                # 限制历史记录长度
                if len(stats.status_history) > config.max_status_history:
                    stats.status_history = stats.status_history[
                        -config.max_status_history :
                    ]

        except Exception as e:
            logger.error(f"Error collecting current stats: {e}")

    async def _aggregate_stats(self):
        """聚合统计数据"""
        try:
            current_hour = datetime.utcnow().strftime("%Y-%m-%d-%H")
            current_day = datetime.utcnow().strftime("%Y-%m-%d")

            # 小时统计
            hour_stats = {
                "device_usage": {
                    device_id: {
                        "total_time": stats.total_usage_time,
                        "session_count": stats.session_count,
                        "error_count": stats.error_count,
                    }
                    for device_id, stats in self.device_stats.items()
                },
                "user_usage": {
                    user_id: {
                        "total_time": stats.total_usage_time,
                        "device_count": stats.device_count,
                        "session_count": stats.session_count,
                    }
                    for user_id, stats in self.user_stats.items()
                },
            }
            self.hourly_stats[current_hour] = hour_stats

            # 日统计
            day_stats = {
                "total_usage_time": sum(
                    stats.total_usage_time for stats in self.device_stats.values()
                ),
                "total_sessions": sum(
                    stats.session_count for stats in self.device_stats.values()
                ),
                "active_devices": len(
                    [
                        d
                        for d in device_manager.controller.devices.values()
                        if d["status"] == "in_use"
                    ]
                ),
                "error_count": sum(
                    stats.error_count for stats in self.device_stats.values()
                ),
            }
            self.daily_stats[current_day] = day_stats

            # 清理旧数据
            self._cleanup_old_stats()

        except Exception as e:
            logger.error(f"Error aggregating stats: {e}")

    def _cleanup_old_stats(self):
        """清理旧统计数据"""
        try:
            now = datetime.utcnow()

            # 保留最近48小时的小时统计
            cutoff_hour = (now - timedelta(hours=48)).strftime("%Y-%m-%d-%H")
            self.hourly_stats = {
                k: v for k, v in self.hourly_stats.items() if k >= cutoff_hour
            }

            # 保留最近30天的日统计
            cutoff_day = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            self.daily_stats = {
                k: v for k, v in self.daily_stats.items() if k >= cutoff_day
            }

        except Exception as e:
            logger.error(f"Error cleaning up old stats: {e}")

    def get_device_stats(self, device_id: str) -> Optional[DeviceStats]:
        """获取设备统计"""
        return self.device_stats.get(device_id)

    def get_user_stats(self, user_id: str) -> Optional[UserStats]:
        """获取用户统计"""
        return self.user_stats.get(user_id)

    def get_hourly_stats(
        self, start_hour: Optional[str] = None, end_hour: Optional[str] = None
    ) -> Dict[str, Dict]:
        """获取小时统计"""
        stats = self.hourly_stats
        if start_hour:
            stats = {k: v for k, v in stats.items() if k >= start_hour}
        if end_hour:
            stats = {k: v for k, v in stats.items() if k <= end_hour}
        return stats

    def get_daily_stats(
        self, start_day: Optional[str] = None, end_day: Optional[str] = None
    ) -> Dict[str, Dict]:
        """获取日统计"""
        stats = self.daily_stats
        if start_day:
            stats = {k: v for k, v in stats.items() if k >= start_day}
        if end_day:
            stats = {k: v for k, v in stats.items() if k <= end_day}
        return stats


# 创建全局统计收集器实例
statistics_collector = StatisticsCollector()
