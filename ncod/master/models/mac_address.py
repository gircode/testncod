from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import select
from ..database import Base, async_session


class MacAddress(Base):
    __tablename__ = "mac_addresses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address = Column(String(17), unique=True, nullable=False)  # FF:FF:FF:FF:FF:FF
    registered_at = Column(DateTime, nullable=False, default=datetime.now)
    last_used = Column(DateTime, nullable=False, default=datetime.now)
    is_active = Column(Boolean, nullable=False, default=True)

    user = relationship("User", back_populates="mac_addresses")

    @classmethod
    async def get_by_address(cls, address: str) -> Optional["MacAddress"]:
        """通过MAC地址获取记录"""
        async with async_session() as session:
            result = await session.execute(select(cls).where(cls.address == address))
            return result.scalar_one_or_none()

    @classmethod
    async def get_by_user_id(cls, user_id: int) -> List["MacAddress"]:
        """获取用户的所有MAC地址"""
        async with async_session() as session:
            result = await session.execute(select(cls).where(cls.user_id == user_id))
            return result.scalars().all()

    @classmethod
    async def cleanup_inactive(cls, before_date: datetime) -> int:
        """清理指定日期前未使用的MAC地址"""
        async with async_session() as session:
            result = await session.execute(
                select(cls).where(
                    (cls.last_used < before_date) & (cls.is_active == True)
                )
            )
            inactive_macs = result.scalars().all()

            for mac in inactive_macs:
                mac.is_active = False

            await session.commit()
            return len(inactive_macs)

    async def save(self):
        """保存或更新MAC地址记录"""
        async with async_session() as session:
            session.add(self)
            await session.commit()
            await session.refresh(self)
