from typing import List, Dict, Any
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ncod.master.models.device import Device
from ncod.master.models.organization import Organization
from ncod.master.models.user import User
from ncod.master.services.cache_manager import CacheManager
from ncod.master.services.device_stats import DeviceStatsService

logger = logging.getLogger(__name__)


class WarmupProgress:
    def __init__(self):
        self.total = 0
        self.completed = 0
        self.current_type = ""
        self.errors = []

    def update(self, completed: int, total: int, current_type: str):
        self.completed = completed
        self.total = total
        self.current_type = current_type

    def add_error(self, error: str):
        self.errors.append(error)

    @property
    def percentage(self) -> float:
        return round(self.completed / self.total * 100, 2) if self.total > 0 else 0

    def to_dict(self) -> Dict:
        return {
            "completed": self.completed,
            "total": self.total,
            "percentage": self.percentage,
            "current_type": self.current_type,
            "errors": self.errors,
        }


class CacheWarmupService:
    def __init__(self, db: Session, cache_manager: CacheManager):
        self.db = db
        self.cache = cache_manager
        self.stats_service = DeviceStatsService(db, cache_manager)
        self.progress = WarmupProgress()

    async def warmup_all(self):
        """预热所有缓存"""
        logger.info("Starting cache warmup...")
        start_time = datetime.utcnow()

        tasks = [
            self.warmup_organizations(),
            self.warmup_devices(),
            self.warmup_device_stats(),
            self.warmup_user_stats(),
        ]

        await asyncio.gather(*tasks)

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Cache warmup completed in {duration:.2f} seconds")

    async def warmup_organizations(self):
        """预热组织数据"""
        orgs = self.db.query(Organization).all()
        total = len(orgs)
        self.progress.update(0, total, "organizations")

        for i, org in enumerate(orgs, 1):
            try:
                key = f"org:{org.id}"
                await self.cache.get_or_set(
                    "long", key, lambda: org.to_dict(), ttl=3600
                )
                self.progress.update(i, total, "organizations")
            except Exception as e:
                self.progress.add_error(f"Error warming up org {org.id}: {str(e)}")

    async def warmup_devices(self):
        """预热设备数据"""
        devices = self.db.query(Device).filter(Device.is_active == True).all()
        for device in devices:
            key = f"device:{device.id}"
            await self.cache.get_or_set("short", key, lambda: device.to_dict(), ttl=300)

    async def warmup_device_stats(self):
        """预热设备统计数据"""
        devices = self.db.query(Device).filter(Device.is_active == True).all()
        for device in devices:
            key = f"device_stats:{device.id}"
            await self.cache.get_or_set(
                "stats",
                key,
                lambda: self.stats_service._fetch_device_stats(device.id),
                ttl=600,
            )

    async def warmup_user_stats(self):
        """预热用户统计数据"""
        active_users = (
            self.db.query(User)
            .filter(User.is_active == True)
            .filter(User.last_login >= datetime.utcnow() - timedelta(days=7))
            .all()
        )

        for user in active_users:
            key = f"user_stats:{user.id}"
            await self.cache.get_or_set(
                "stats", key, lambda: self._get_user_stats(user.id), ttl=600
            )

    def _get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户统计数据"""
        from ncod.master.models.device_history import DeviceHistory

        # 获取最近30天的使用记录
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        usage_records = (
            self.db.query(DeviceHistory)
            .filter(
                DeviceHistory.user_id == user_id,
                DeviceHistory.created_at >= thirty_days_ago,
            )
            .all()
        )

        # 计算总使用时长
        total_duration = sum(
            (r.end_time - r.start_time).total_seconds() / 3600
            for r in usage_records
            if r.end_time
        )

        # 计算设备使用分布
        device_usage = {}
        for record in usage_records:
            device_id = record.device_id
            if device_id not in device_usage:
                device_usage[device_id] = 0
            if record.end_time:
                duration = (record.end_time - record.start_time).total_seconds() / 3600
                device_usage[device_id] += duration

        # 计算使用时段分布
        hour_distribution = [0] * 24
        for record in usage_records:
            hour = record.start_time.hour
            hour_distribution[hour] += 1

        return {
            "total_duration": round(total_duration, 2),
            "usage_count": len(usage_records),
            "device_usage": device_usage,
            "hour_distribution": hour_distribution,
            "last_updated": datetime.utcnow(),
        }
