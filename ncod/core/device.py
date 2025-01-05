"""设备服务模块"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ncod.core.db import db
from ncod.models.device import Device
from ncod.schemas.device import DeviceCreate, DeviceUpdate
from ncod.utils.logger import logger


class DeviceService:
    """设备服务类"""

    @staticmethod
    async def get_devices(
        user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Device]:
        """获取设备列表"""
        async with db.async_session() as session:
            result = await session.execute(
                select(Device)
                .where(Device.user_id == user_id)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()

    @staticmethod
    async def create_device(user_id: int, device_data: DeviceCreate) -> Device:
        """创建设备"""
        async with db.async_session() as session:
            device = Device(user_id=user_id, **device_data.model_dump())
            session.add(device)
            await session.commit()
            await session.refresh(device)
            return device

    @staticmethod
    async def get_device(user_id: int, device_id: int) -> Optional[Device]:
        """获取设备详情"""
        async with db.async_session() as session:
            result = await session.execute(
                select(Device)
                .where(Device.id == device_id)
                .where(Device.user_id == user_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def update_device(
        user_id: int, device_id: int, device_data: DeviceUpdate
    ) -> Optional[Device]:
        """更新设备"""
        async with db.async_session() as session:
            device = await DeviceService.get_device(user_id, device_id)
            if not device:
                return None

            update_data = device_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(device, field, value)

            await session.commit()
            await session.refresh(device)
            return device

    @staticmethod
    async def delete_device(user_id: int, device_id: int) -> bool:
        """删除设备"""
        async with db.async_session() as session:
            device = await DeviceService.get_device(user_id, device_id)
            if not device:
                return False

            await session.delete(device)
            await session.commit()
            return True
