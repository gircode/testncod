"""设备使用统计服务"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from ncod.core.logger import setup_logger
from ncod.core.db.transaction import transaction_manager
from ncod.master.models.device_usage import DeviceUsage
from ncod.master.models.device import Device
from ncod.master.database import get_session

logger = setup_logger("device_stats")


class DeviceStatsService:
    """设备使用统计服务"""

    def __init__(self):
        self.transaction = transaction_manager

    @staticmethod
    async def get_device_stats(device_id: str):
        async with get_session() as session:
            query = (
                select(DeviceStats)
                .where(DeviceStats.device_id == device_id)
                .order_by(desc(DeviceStats.created_at))
                .limit(1)
            )
            result = await session.execute(query)
            return result.scalars().first()

    @staticmethod
    async def get_device_history(
        device_id: str, start_time: datetime, end_time: datetime
    ):
        async with get_session() as session:
            query = (
                select(DeviceUsageStats)
                .where(
                    DeviceUsageStats.device_id == device_id,
                    DeviceUsageStats.created_at.between(start_time, end_time),
                )
                .order_by(DeviceUsageStats.created_at)
            )
            result = await session.execute(query)
            return result.scalars().all()


# 创建全局设备统计服务实例
device_stats_service = DeviceStatsService()
