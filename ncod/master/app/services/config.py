"""
配置服务
"""

from typing import List, Optional, Sequence

from app.models.config import Config
from app.schemas.config import ConfigCreate, ConfigSearch, ConfigUpdate
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import expression


class ConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_configs(self, search: ConfigSearch) -> List[Config]:
        """获取配置列表"""
        query = select(Config)

        if search.key:
            query = query.where(
                expression.text("configs.key ILIKE :key").bindparams(
                    key=f"%{search.key}%"
                )
            )
        if search.group:
            query = query.where(
                expression.text("configs.group = :group").bindparams(group=search.group)
            )
        if search.is_secret is not None:
            query = query.where(
                expression.text("configs.is_secret = :is_secret").bindparams(
                    is_secret=search.is_secret
                )
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_config(self, key: str) -> Optional[Config]:
        """获取配置"""
        query = select(Config).where(
            expression.text("configs.key = :key").bindparams(key=key)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_config(self, config_in: ConfigCreate) -> Config:
        """创建配置"""
        config = Config(**config_in.dict())
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def update_config(
        self, key: str, config_in: ConfigUpdate
    ) -> Optional[Config]:
        """更新配置"""
        config = await self.get_config(key)
        if not config:
            return None

        for field, value in config_in.dict(exclude_unset=True).items():
            setattr(config, field, value)

        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def delete_config(self, key: str) -> bool:
        """删除配置"""
        config = await self.get_config(key)
        if not config:
            return False

        await self.db.delete(config)
        await self.db.commit()
        return True
