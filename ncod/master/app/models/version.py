"""
配置版本控制模型
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    select,
    update,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base_class import Base
from .models import SystemConfig, User

logger = logging.getLogger(__name__)


class ConfigVersion(Base):
    """配置版本"""

    __tablename__ = "config_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    creator: Mapped[User] = relationship(back_populates="config_versions")

    def __repr__(self) -> str:
        return f"<ConfigVersion {self.config_key}@{self.version}>"


class VersionManager:
    """版本管理器"""

    def __init__(self, db_session):
        self.db = db_session

    async def create_version(
        self,
        config_key: str,
        value: str,
        user_id: int,
        metadata: Optional[Dict] = None,
        comment: Optional[str] = None,
        activate: bool = True,
    ) -> ConfigVersion:
        """创建新版本"""
        try:
            # 获取当前最新版本号
            query = select(func.max(ConfigVersion.version)).where(
                ConfigVersion.config_key == config_key
            )
            result = await self.db.execute(query)
            current_version = result.scalar() or 0

            # 创建新版本
            version = ConfigVersion(
                config_key=config_key,
                version=current_version + 1,
                value=value,
                metadata=metadata,
                comment=comment,
                is_active=activate,
                created_by=user_id,
            )

            if activate:
                # 取消其他版本的活动状态
                await self.db.execute(
                    update(ConfigVersion)
                    .where(
                        ConfigVersion.config_key == config_key,
                        ConfigVersion.is_active == True,
                    )
                    .values(is_active=False)
                )

            self.db.add(version)
            await self.db.commit()
            await self.db.refresh(version)

            return version

        except Exception as e:
            logger.error(f"创建版本失败: {str(e)}")
            await self.db.rollback()
            raise

    async def get_version(
        self, config_key: str, version: Optional[int] = None
    ) -> Optional[ConfigVersion]:
        """获取指定版本"""
        try:
            query = select(ConfigVersion).where(ConfigVersion.config_key == config_key)

            if version is not None:
                # 获取指定版本
                query = query.where(ConfigVersion.version == version)
            else:
                # 获取当前活动版本
                query = query.where(ConfigVersion.is_active == True)

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"获取版本失败: {str(e)}")
            raise

    async def list_versions(
        self, config_key: str, skip: int = 0, limit: int = 100
    ) -> List[ConfigVersion]:
        """获取版本列表"""
        try:
            query = (
                select(ConfigVersion)
                .where(ConfigVersion.config_key == config_key)
                .order_by(ConfigVersion.version.desc())
                .offset(skip)
                .limit(limit)
            )

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"获取版本列表失败: {str(e)}")
            raise

    async def activate_version(
        self, config_key: str, version: int, user_id: int
    ) -> bool:
        """激活指定版本"""
        try:
            # 检查版本是否存在
            target_version = await self.get_version(config_key, version)
            if not target_version:
                raise ValueError(f"版本不存在: {version}")

            async with self.db.begin():
                # 取消当前活动版本
                await self.db.execute(
                    update(ConfigVersion)
                    .where(
                        ConfigVersion.config_key == config_key,
                        ConfigVersion.is_active == True,
                    )
                    .values(is_active=False)
                )

                # 激活目标版本
                target_version.is_active = True

                # 更新配置值
                await self.db.execute(
                    update(SystemConfig)
                    .where(SystemConfig.key == config_key)
                    .values(
                        value=target_version.value,
                        updated_by=user_id,
                        updated_at=datetime.utcnow(),
                    )
                )

            return True

        except Exception as e:
            logger.error(f"激活版本失败: {str(e)}")
            await self.db.rollback()
            raise

    async def compare_versions(
        self, config_key: str, version1: int, version2: int
    ) -> Dict[str, Any]:
        """比较两个版本"""
        try:
            # 获取两个版本
            v1 = await self.get_version(config_key, version1)
            v2 = await self.get_version(config_key, version2)

            if not v1 or not v2:
                raise ValueError("版本不存在")

            # 比较差异
            return {
                "version1": {
                    "version": v1.version,
                    "value": v1.value,
                    "metadata": v1.metadata,
                    "created_at": v1.created_at,
                    "created_by": v1.created_by,
                },
                "version2": {
                    "version": v2.version,
                    "value": v2.value,
                    "metadata": v2.metadata,
                    "created_at": v2.created_at,
                    "created_by": v2.created_by,
                },
            }

        except Exception as e:
            logger.error(f"比较版本失败: {str(e)}")
            raise
