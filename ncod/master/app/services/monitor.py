"""
主服务器监控服务
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

import aiohttp
from aiohttp import ClientTimeout
from ncod.common.models.monitor import MonitorAlert, MonitorMetric
from ncod.common.services.monitor import BaseMonitorService
from ncod.master.app.core.config import settings
from ncod.master.app.models.device import Device, GroupRelation, SlaveServer
from ncod.master.app.models.monitor import DeviceUsage
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MonitorService(BaseMonitorService):
    """主服务器监控服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self._device_locks: Dict[int, asyncio.Lock] = {}
        self._group_device_mapping: Dict[int, Set[int]] = {}
        self._cleanup_lock = asyncio.Lock()
        self._request_timeout = ClientTimeout(total=settings.REQUEST_TIMEOUT)

    async def initialize(self):
        """初始化监控服务"""
        if self._running:
            return

        await super().start()
        self._tasks = [
            asyncio.create_task(self._check_slave_health()),
            asyncio.create_task(self._monitor_device_usage()),
        ]

    async def shutdown(self):
        """关闭监控服务"""
        await super().stop()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []

    async def _cleanup_old_data(self):
        """清理旧数据"""
        try:
            async with self._cleanup_lock:
                # 清理超过保留期限的监控指标
                metrics_retention_date = datetime.utcnow() - timedelta(
                    days=settings.METRICS_RETENTION_DAYS
                )
                await self.db.execute(
                    delete(MonitorMetric).where(
                        MonitorMetric.timestamp < metrics_retention_date
                    )
                )

                # 清理已解决的告警
                alert_retention_date = datetime.utcnow() - timedelta(
                    days=settings.ALERT_RETENTION_DAYS
                )
                await self.db.execute(
                    delete(MonitorAlert).where(
                        and_(
                            MonitorAlert.resolved == True,
                            MonitorAlert.created_at < alert_retention_date,
                        )
                    )
                )

                # 清理设备使用记录
                usage_retention_date = datetime.utcnow() - timedelta(
                    days=settings.USAGE_RETENTION_DAYS
                )
                await self.db.execute(
                    delete(DeviceUsage).where(
                        DeviceUsage.end_time < usage_retention_date
                    )
                )

                await self.db.commit()
        except Exception as e:
            logger.error(f"清理旧数据失败: {str(e)}")
            await self.db.rollback()

    async def _check_slave_health(self):
        """检查从服务器健康状态"""
        while self._running:
            try:
                query = select(SlaveServer)
                result = await self.db.execute(query)
                slaves = result.scalars().all()

                async with aiohttp.ClientSession(
                    timeout=self._request_timeout
                ) as session:
                    for slave in slaves:
                        try:
                            async with session.get(
                                f"http://{slave.host}:{slave.port}/health"
                            ) as response:
                                if response.status != 200:
                                    await self._create_alert(
                                        alert_type="slave_health",
                                        severity="critical",
                                        message=f"从服务器 {slave.host}:{slave.port} \
                                             健康检查失败",
                                        metadata={
                                            "slave_id": slave.id,
                                            "status_code": response.status,
                                        },
                                    )
                        except Exception as e:
                            await self._create_alert(
                                alert_type="slave_health",
                                severity="critical",
                                message=f"从服务器 {slave.host}:{slave.port} 连接失败: \
                                     {str(e)}",
                                metadata={"slave_id": slave.id},
                            )

            except Exception as e:
                logger.error(f"检查从服务器健康状态失败: {str(e)}")

            await asyncio.sleep(settings.SLAVE_HEALTH_CHECK_INTERVAL)

    async def _monitor_device_usage(self):
        """监控设备使用情况"""
        while self._running:
            try:
                # 检查设备使用时间是否超限
                query = select(DeviceUsage).where(
                    and_(
                        DeviceUsage.end_time.is_(None),
                        DeviceUsage.start_time
                        <= datetime.utcnow()
                        - timedelta(hours=settings.MAX_DEVICE_USAGE_HOURS),
                    )
                )
                result = await self.db.execute(query)
                overused_devices = result.scalars().all()

                for usage in overused_devices:
                    await self._create_alert(
                        alert_type="device_usage",
                        severity="warning",
                        message=f"设备 {usage.device_id} 使用时间超过 \
                             {settings.MAX_DEVICE_USAGE_HOURS} 小时",
                        metadata={"device_id": usage.device_id, "usage_id": usage.id},
                    )

            except Exception as e:
                logger.error(f"监控设备使用情况失败: {str(e)}")

            await asyncio.sleep(settings.DEVICE_USAGE_CHECK_INTERVAL)

    async def check_device_sharing(self, device_id: int, group_id: int) -> bool:
        """检查设备是否可以被指定组使用"""
        try:
            # 检查设备当前是否被其他组占用
            if device_id in self._group_device_mapping:
                current_group = next(
                    (
                        g
                        for g, devices in self._group_device_mapping.items()
                        if device_id in devices
                    ),
                    None,
                )
                if current_group and current_group != group_id:
                    # 检查组间是否允许共享
                    query = select(GroupRelation).where(
                        and_(
                            GroupRelation.group_id == current_group,
                            GroupRelation.related_group_id == group_id,
                            GroupRelation.allow_device_sharing == True,
                        )
                    )
                    result = await self.db.execute(query)
                    relation = result.scalar_one_or_none()
                    return relation is not None

            return True

        except Exception as e:
            logger.error(f"检查设备共享失败: {str(e)}")
            return False

    async def acquire_device(self, device_id: int, group_id: int) -> bool:
        """尝试获取设备使用权"""
        if device_id not in self._device_locks:
            self._device_locks[device_id] = asyncio.Lock()

        async with self._device_locks[device_id]:
            if not await self.check_device_sharing(device_id, group_id):
                return False

            if group_id not in self._group_device_mapping:
                self._group_device_mapping[group_id] = set()

            self._group_device_mapping[group_id].add(device_id)
            return True

    async def release_device(self, device_id: int, group_id: int):
        """释放设备使用权"""
        if device_id in self._device_locks:
            async with self._device_locks[device_id]:
                if group_id in self._group_device_mapping:
                    self._group_device_mapping[group_id].discard(device_id)

    async def get_available_devices(self, group_id: int) -> List[int]:
        """获取组可用的设备列表"""
        try:
            # 获取本组设备
            query = select(Device).where(Device.group_id == group_id)
            result = await self.db.execute(query)
            own_devices = set(d.id for d in result.scalars().all())

            # 获取可共享的其他组设备
            query = (
                select(Device)
                .join(
                    GroupRelation,
                    and_(
                        GroupRelation.related_group_id == group_id,
                        GroupRelation.allow_device_sharing == True,
                    ),
                )
                .where(Device.group_id == GroupRelation.group_id)
            )
            result = await self.db.execute(query)
            shared_devices = set(d.id for d in result.scalars().all())

            return list(own_devices | shared_devices)

        except Exception as e:
            logger.error(f"获取可用设备失败: {str(e)}")
            return []

    async def check_device_status(self, device_id: int) -> Dict:
        """检查设备状态"""
        try:
            # 获取设备信息
            query = select(Device).where(Device.id == device_id)
            result = await self.db.execute(query)
            device = result.scalar_one_or_none()

            if not device:
                return {"is_active": False, "error": "设备不存在"}

            # 检查设备是否在线
            if device.slave_server:
                async with aiohttp.ClientSession(
                    timeout=self._request_timeout
                ) as session:
                    async with session.get(
                        f"http://{device.slave_server.host}:{device.slave_server.port}/d \
                             \
                             \
                             \
                            evice/{device.virtualhere_id}/status"
                    ) as response:
                        if response.status == 200:
                            status_data = await response.json()
                            return {
                                "is_active": status_data.get("is_active", False),
                                "status": status_data.get("status"),
                                "current_user": status_data.get("current_user"),
                            }

            return {"is_active": False, "error": "无法获取设备状态"}

        except Exception as e:
            logger.error(f"检查设备状态失败: {str(e)}")
            return {"is_active": False, "error": str(e)}

    async def get_device_usage_stats(
        self,
        device_id: Optional[int] = None,
        group_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict:
        """获取设备使用统计"""
        try:
            query = select(DeviceUsage)

            if device_id:
                query = query.where(DeviceUsage.device_id == device_id)

            if group_id:
                query = query.where(DeviceUsage.group_id == group_id)

            if start_time:
                query = query.where(DeviceUsage.start_time >= start_time)

            if end_time:
                query = query.where(DeviceUsage.end_time <= end_time)

            result = await self.db.execute(query)
            usage_records = result.scalars().all()

            # 计算总使用时间
            total_usage_time = timedelta()
            for record in usage_records:
                if record.end_time:
                    total_usage_time += record.end_time - record.start_time
                else:
                    total_usage_time += datetime.utcnow() - record.start_time

            # 计算使用率
            if start_time and end_time:
                total_time = end_time - start_time
            else:
                total_time = timedelta(days=30)  # 默认统计30天

            usage_rate = (
                total_usage_time.total_seconds() / total_time.total_seconds()
            ) * 100

            return {
                "total_usage_time": total_usage_time.total_seconds(),
                "usage_rate": usage_rate,
                "total_records": len(usage_records),
                "active_records": sum(1 for r in usage_records if not r.end_time),
            }

        except Exception as e:
            logger.error(f"获取设备使用统计失败: {str(e)}")
            return {
                "total_usage_time": 0,
                "usage_rate": 0,
                "total_records": 0,
                "active_records": 0,
            }

    async def get_device_status_summary(self) -> Dict:
        """获取设备状态汇总"""
        try:
            # 获取所有设备
            query = select(Device)
            result = await self.db.execute(query)
            devices = result.scalars().all()

            total_devices = len(devices)
            active_devices = 0
            offline_devices = 0
            in_use_devices = 0

            for device in devices:
                status = await self.check_device_status(device.id)
                if status["is_active"]:
                    active_devices += 1
                    if status.get("current_user"):
                        in_use_devices += 1
                else:
                    offline_devices += 1

            return {
                "total_devices": total_devices,
                "active_devices": active_devices,
                "offline_devices": offline_devices,
                "in_use_devices": in_use_devices,
                "available_devices": active_devices - in_use_devices,
                "utilization_rate": (
                    (in_use_devices / total_devices * 100) if total_devices > 0 else 0
                ),
            }

        except Exception as e:
            logger.error(f"获取设备状态汇总失败: {str(e)}")
            return {
                "total_devices": 0,
                "active_devices": 0,
                "offline_devices": 0,
                "in_use_devices": 0,
                "available_devices": 0,
                "utilization_rate": 0,
            }

    async def get_device_usage_history(
        self,
        device_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """获取设备使用历史"""
        try:
            query = select(DeviceUsage).where(DeviceUsage.device_id == device_id)

            if start_time:
                query = query.where(DeviceUsage.start_time >= start_time)

            if end_time:
                query = query.where(DeviceUsage.end_time <= end_time)

            query = query.order_by(DeviceUsage.start_time.desc()).limit(limit)

            result = await self.db.execute(query)
            usage_records = result.scalars().all()

            history = []
            for record in usage_records:
                duration = None
                if record.end_time:
                    duration = (record.end_time - record.start_time).total_seconds()

                history.append(
                    {
                        "id": record.id,
                        "user_id": record.user_id,
                        "group_id": record.group_id,
                        "start_time": record.start_time.isoformat(),
                        "end_time": (
                            record.end_time.isoformat() if record.end_time else None
                        ),
                        "duration": duration,
                    }
                )

            return history

        except Exception as e:
            logger.error(f"获取设备使用历史失败: {str(e)}")
            return []

    async def get_group_device_stats(self, group_id: int) -> Dict:
        """获取组设备统计"""
        try:
            # 获取组内设备
            query = select(Device).where(Device.group_id == group_id)
            result = await self.db.execute(query)
            devices = result.scalars().all()

            total_devices = len(devices)
            active_devices = 0
            offline_devices = 0
            in_use_devices = 0

            # 获取设备使用统计
            usage_stats = await self.get_device_usage_stats(group_id=group_id)

            for device in devices:
                status = await self.check_device_status(device.id)
                if status["is_active"]:
                    active_devices += 1
                    if status.get("current_user"):
                        in_use_devices += 1
                else:
                    offline_devices += 1

            return {
                "total_devices": total_devices,
                "active_devices": active_devices,
                "offline_devices": offline_devices,
                "in_use_devices": in_use_devices,
                "available_devices": active_devices - in_use_devices,
                "utilization_rate": (
                    (in_use_devices / total_devices * 100) if total_devices > 0 else 0
                ),
                "total_usage_time": usage_stats["total_usage_time"],
                "usage_rate": usage_stats["usage_rate"],
            }

        except Exception as e:
            logger.error(f"获取组设备统计失败: {str(e)}")
            return {
                "total_devices": 0,
                "active_devices": 0,
                "offline_devices": 0,
                "in_use_devices": 0,
                "available_devices": 0,
                "utilization_rate": 0,
                "total_usage_time": 0,
                "usage_rate": 0,
            }
