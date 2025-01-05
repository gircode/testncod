"""设备使用记录服务"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from ncod.core.db.database import get_db
from ncod.core.logger import setup_logger
from ncod.master.models.device_usage import DeviceUsage
from ncod.master.schemas.device_usage import DeviceUsageCreate, DeviceUsageUpdate

logger = setup_logger("device_usage_service")


class DeviceUsageService:
    """设备使用记录服务"""

    async def get_device_usage(self, usage_id: str) -> Optional[DeviceUsage]:
        """获取使用记录"""
        async for db in get_db():
            stmt = (
                select(DeviceUsage)
                .where(DeviceUsage.id == usage_id)
                .options(
                    selectinload(DeviceUsage.device), selectinload(DeviceUsage.user)
                )
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()

    async def get_device_usage_logs(
        self,
        device_id: Optional[str] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DeviceUsage]:
        """获取使用记录列表"""
        async with get_db() as db:
            stmt = select(DeviceUsage).options(
                selectinload(DeviceUsage.device), selectinload(DeviceUsage.user)
            )

            # 添加过滤条件
            conditions = []
            if device_id:
                conditions.append(DeviceUsage.device_id == device_id)
            if user_id:
                conditions.append(DeviceUsage.user_id == user_id)
            if conditions:
                stmt = stmt.where(and_(*conditions))

            # 添加分页
            stmt = stmt.offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())

    async def create_device_usage(
        self, user_id: str, usage_data: DeviceUsageCreate
    ) -> DeviceUsage:
        """创建使用记录"""
        async with get_db() as db:
            # 检查设备是否已被使用
            active_usage = await self.get_active_device_usage(usage_data.device_id)
            if active_usage:
                raise ValueError("Device is already in use")

            # 创建使用记录
            db_usage = DeviceUsage(
                user_id=user_id,
                device_id=usage_data.device_id,
                connection_info=usage_data.connection_info,
                start_time=datetime.utcnow(),
                status="active",
            )
            db.add(db_usage)
            await db.commit()
            await db.refresh(db_usage)
            return db_usage

    async def update_device_usage(
        self, usage_id: str, usage_update: DeviceUsageUpdate
    ) -> Optional[DeviceUsage]:
        """更新使用记录"""
        async with get_db() as db:
            # 获取使用记录
            stmt = select(DeviceUsage).where(DeviceUsage.id == usage_id)
            result = await db.execute(stmt)
            usage = result.scalar_one_or_none()
            if not usage:
                return None

            # 更新记录
            update_data = usage_update.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(usage, key, value)

            await db.commit()
            await db.refresh(usage)
            return usage

    async def get_active_device_usage(self, device_id: str) -> Optional[DeviceUsage]:
        """获取设备当前使用记录"""
        async with get_db() as db:
            stmt = select(DeviceUsage).where(
                and_(DeviceUsage.device_id == device_id, DeviceUsage.status == "active")
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()

    async def end_device_usage(
        self, usage_id: str, status: str = "completed"
    ) -> Optional[DeviceUsage]:
        """结束设备使用"""
        return await self.update_device_usage(
            usage_id, DeviceUsageUpdate(end_time=datetime.utcnow(), status=status)
        )
