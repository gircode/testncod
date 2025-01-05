"""设备服务"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from ...models.device import Device, DevicePort
from ...schemas.device import DeviceCreate, DeviceUpdate, DevicePortCreate
from ...utils.logger import logger


class DeviceService:
    """设备服务类"""

    @staticmethod
    async def get_device(db: AsyncSession, device_id: int) -> Optional[Device]:
        """获取设备"""
        try:
            result = await db.execute(select(Device).where(Device.id == device_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("获取设备失败", exc_info=True)
            raise

    @staticmethod
    async def get_user_devices(db: AsyncSession, user_id: int) -> List[Device]:
        """获取用户的设备列表"""
        try:
            result = await db.execute(select(Device).where(Device.owner_id == user_id))
            return result.scalars().all()
        except Exception as e:
            logger.error("获取用户设备列表失败", exc_info=True)
            raise

    @staticmethod
    async def create_device(db: AsyncSession, device_data: DeviceCreate) -> Device:
        """创建设备"""
        try:
            device = Device(**device_data.model_dump())
            db.add(device)
            await db.commit()
            await db.refresh(device)
            return device
        except Exception as e:
            await db.rollback()
            logger.error("创建设备失败", exc_info=True)
            raise

    @staticmethod
    async def update_device(
        db: AsyncSession, device_id: int, device_data: DeviceUpdate
    ) -> Optional[Device]:
        """更新设备"""
        try:
            result = await db.execute(select(Device).where(Device.id == device_id))
            device = result.scalar_one_or_none()
            if not device:
                return None

            update_data = device_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(device, field, value)

            await db.commit()
            await db.refresh(device)
            return device
        except Exception as e:
            await db.rollback()
            logger.error("更新设备失败", exc_info=True)
            raise

    @staticmethod
    async def delete_device(db: AsyncSession, device_id: int) -> bool:
        """删除设备"""
        try:
            result = await db.execute(select(Device).where(Device.id == device_id))
            device = result.scalar_one_or_none()
            if not device:
                return False

            await db.delete(device)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error("删除设备失败", exc_info=True)
            raise
