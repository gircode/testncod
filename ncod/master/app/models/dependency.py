"""
配置依赖关系模型
"""

import logging
from datetime import datetime
from typing import List, Optional, Set

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    delete,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base_class import Base

logger = logging.getLogger(__name__)


class ConfigDependency(Base):
    """配置依赖关系"""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    depends_on: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # 关系
    creator = relationship("User")

    # 约束
    __table_args__ = (
        UniqueConstraint("config_key", "depends_on", name="uq_config_dependency"),
    )

    def __repr__(self) -> str:
        return f"<ConfigDependency {self.config_key} -> {self.depends_on}>"


class DependencyManager:
    """依赖关系管理器"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def add_dependency(
        self, config_key: str, depends_on: str, user_id: int
    ) -> ConfigDependency:
        """添加依赖关系"""
        try:
            # 检查循环依赖
            if await self._has_circular_dependency(config_key, depends_on):
                raise ValueError("检测到循环依赖")

            # 创建依赖关系
            dependency = ConfigDependency(
                config_key=config_key, depends_on=depends_on, created_by=user_id
            )

            self.db.add(dependency)
            await self.db.commit()
            await self.db.refresh(dependency)

            return dependency

        except Exception as e:
            logger.error(f"添加依赖关系失败: {str(e)}")
            await self.db.rollback()
            raise

    async def remove_dependency(self, config_key: str, depends_on: str) -> bool:
        """移除依赖关系"""
        try:
            result = await self.db.execute(
                delete(ConfigDependency).where(
                    ConfigDependency.config_key == config_key,
                    ConfigDependency.depends_on == depends_on,
                )
            )

            await self.db.commit()
            return result.rowcount > 0

        except Exception as e:
            logger.error(f"移除依赖关系失败: {str(e)}")
            await self.db.rollback()
            raise

    async def get_dependencies(
        self, config_key: str, recursive: bool = False
    ) -> List[str]:
        """获取配置的依赖项"""
        try:
            if recursive:
                return await self._get_recursive_dependencies(config_key)

            query = select(ConfigDependency.depends_on).where(
                ConfigDependency.config_key == config_key
            )
            result = await self.db.execute(query)
            return [row[0] for row in result]

        except Exception as e:
            logger.error(f"获取依赖项失败: {str(e)}")
            raise

    async def get_dependents(
        self, config_key: str, recursive: bool = False
    ) -> List[str]:
        """获取依赖于该配置的项"""
        try:
            if recursive:
                return await self._get_recursive_dependents(config_key)

            query = select(ConfigDependency.config_key).where(
                ConfigDependency.depends_on == config_key
            )
            result = await self.db.execute(query)
            return [row[0] for row in result]

        except Exception as e:
            logger.error(f"获取依赖方失败: {str(e)}")
            raise

    async def validate_dependencies(self, config_key: str) -> List[str]:
        """验证依赖项是否都存在"""
        try:
            # 获取所有依赖项
            dependencies = await self.get_dependencies(config_key, recursive=True)

            # 检查依赖项是否存在
            query = select(SystemConfig.key).where(SystemConfig.key.in_(dependencies))
            result = await self.db.execute(query)
            existing = {row[0] for row in result}

            # 返回不存在的依赖项
            return [dep for dep in dependencies if dep not in existing]

        except Exception as e:
            logger.error(f"验证依赖项失败: {str(e)}")
            raise

    async def _has_circular_dependency(self, config_key: str, depends_on: str) -> bool:
        """检查是否存在循环依赖"""
        try:
            # 获取被依赖方的所有依赖项
            dependencies = await self._get_recursive_dependencies(depends_on)

            # 如果依赖方出现在被依赖方的依赖树中，则存在循环依赖
            return config_key in dependencies

        except Exception as e:
            logger.error(f"检查循环依赖失败: {str(e)}")
            raise

    async def _get_recursive_dependencies(
        self, config_key: str, visited: Optional[Set[str]] = None
    ) -> List[str]:
        """递归获取所有依赖项"""
        if visited is None:
            visited = set()

        if config_key in visited:
            return []

        visited.add(config_key)
        result = []

        # 获取直接依赖项
        direct_deps = await self.get_dependencies(config_key)
        result.extend(direct_deps)

        # 递归获取间接依赖项
        for dep in direct_deps:
            indirect_deps = await self._get_recursive_dependencies(dep, visited)
            result.extend(indirect_deps)

        return list(set(result))

    async def _get_recursive_dependents(
        self, config_key: str, visited: Optional[Set[str]] = None
    ) -> List[str]:
        """递归获取所有依赖方"""
        if visited is None:
            visited = set()

        if config_key in visited:
            return []

        visited.add(config_key)
        result = []

        # 获取直接依赖方
        direct_deps = await self.get_dependents(config_key)
        result.extend(direct_deps)

        # 递归获取间接依赖方
        for dep in direct_deps:
            indirect_deps = await self._get_recursive_dependents(dep, visited)
            result.extend(indirect_deps)

        return list(set(result))
