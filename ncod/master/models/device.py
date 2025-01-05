"""设备模型"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, select
from pydantic import BaseModel
from ncod.master.core.database import Base


class DeviceStatus(str, Enum):
    """设备状态枚举"""

    OFFLINE = "offline"
    ONLINE = "online"
    ERROR = "error"


class Device(Base):
    """设备数据库模型"""

    __tablename__ = "devices"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.OFFLINE)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    async def get_all(cls, db):
        """获取所有设备"""
        result = await db.execute(select(cls))
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, db, device_id: str):
        """通过ID获取设备"""
        result = await db.execute(select(cls).where(cls.id == device_id))
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, device_data):
        """创建设备"""
        device = cls(**device_data.dict())
        db.add(device)
        await db.commit()
        await db.refresh(device)
        return device

    @classmethod
    async def update(cls, db, device_id: str, device_data):
        """更新设备"""
        device = await cls.get_by_id(db, device_id)
        if device:
            for key, value in device_data.dict(exclude_unset=True).items():
                setattr(device, key, value)
            await db.commit()
            await db.refresh(device)
        return device

    @classmethod
    async def delete(cls, db, device_id: str):
        """删除设备"""
        device = await cls.get_by_id(db, device_id)
        if device:
            await db.delete(device)
            await db.commit()
            return True
        return False


class DeviceBase(BaseModel):
    """设备基础模型"""

    name: str
    type: str


class DeviceCreate(DeviceBase):
    """设备创建模型"""

    pass


class DeviceUpdate(DeviceBase):
    """设备更新模型"""

    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[DeviceStatus] = None
