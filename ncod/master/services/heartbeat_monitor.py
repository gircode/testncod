import asyncio
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ncod.master.models.heartbeat import HeartbeatRecord
from ncod.master.core.config import settings
from ncod.master.core.logger import logger


class HeartbeatMonitor:
    """心跳监控服务"""

    def __init__(self):
        self.heartbeat_timeout = settings.HEARTBEAT_TIMEOUT
        self.retry_limit = settings.HEARTBEAT_RETRY_LIMIT
        self._running = False
        self._tasks = {}

    async def start(self):
        """启动心跳监控"""
        if self._running:
            return
        self._running = True
        logger.info("Starting heartbeat monitor service")
        asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """停止心跳监控"""
        if not self._running:
            return
        self._running = False
        logger.info("Stopping heartbeat monitor service")
        for task in self._tasks.values():
            task.cancel()

    async def _monitor_loop(self):
        """心跳监控主循环"""
        while self._running:
            try:
                await self._check_heartbeats()
            except Exception as e:
                logger.error(f"Error in heartbeat monitor loop: {e}")
            await asyncio.sleep(self.heartbeat_timeout)

    async def _check_heartbeats(self):
        """检查所有心跳记录"""
        async with AsyncSession() as session:
            stmt = select(HeartbeatRecord).where(
                HeartbeatRecord.last_heartbeat
                < datetime.utcnow() - asyncio.timedelta(seconds=self.heartbeat_timeout)
            )
            result = await session.execute(stmt)
            stale_records = result.scalars().all()

            for record in stale_records:
                if record.retry_count >= self.retry_limit:
                    await self._handle_failed_heartbeat(session, record)
                else:
                    await self._increment_retry_count(session, record)

            await session.commit()

    async def _handle_failed_heartbeat(
        self, session: AsyncSession, record: HeartbeatRecord
    ):
        """处理心跳失败的记录"""
        logger.warning(f"Heartbeat failed for slave {record.slave_id}")
        stmt = (
            update(HeartbeatRecord)
            .where(HeartbeatRecord.id == record.id)
            .values(is_alive=False, retry_count=0)
        )
        await session.execute(stmt)

    async def _increment_retry_count(
        self, session: AsyncSession, record: HeartbeatRecord
    ):
        """增加重试次数"""
        stmt = (
            update(HeartbeatRecord)
            .where(HeartbeatRecord.id == record.id)
            .values(retry_count=record.retry_count + 1)
        )
        await session.execute(stmt)

    async def update_heartbeat(self, slave_id: int):
        """更新心跳时间"""
        async with AsyncSession() as session:
            stmt = (
                update(HeartbeatRecord)
                .where(HeartbeatRecord.slave_id == slave_id)
                .values(last_heartbeat=datetime.utcnow(), retry_count=0, is_alive=True)
            )
            await session.execute(stmt)
            await session.commit()
