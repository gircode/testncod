"""
Slave service module
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.slave import Slave
from ..schemas.slave import SlaveCreate, SlaveUpdate


class SlaveService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_slaves(self) -> list[Slave]:
        result = await self.session.execute(select(Slave))
        return result.scalars().all()

    async def get_slave(self, slave_id: int) -> Slave | None:
        result = await self.session.execute(select(Slave).filter(Slave.id == slave_id))
        return result.scalar_one_or_none()

    async def create_slave(self, slave_data: SlaveCreate) -> Slave:
        slave = Slave(**slave_data.dict())
        self.session.add(slave)
        await self.session.commit()
        await self.session.refresh(slave)
        return slave

    async def update_slave(
        self, slave_id: int, slave_data: SlaveUpdate
    ) -> Slave | None:
        slave = await self.get_slave(slave_id)
        if slave:
            for field, value in slave_data.dict(exclude_unset=True).items():
                setattr(slave, field, value)
            await self.session.commit()
            await self.session.refresh(slave)
        return slave

    async def delete_slave(self, slave_id: int) -> bool:
        slave = await self.get_slave(slave_id)
        if slave:
            await self.session.delete(slave)
            await self.session.commit()
            return True
        return False
