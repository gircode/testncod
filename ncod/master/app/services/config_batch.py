"""配置批量操作服务"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.dependency import DependencyManager
from ..models.system import SystemConfig
from ..models.template import TemplateManager
from ..models.version import VersionManager
from ..schemas.config import ConfigCreate, ConfigUpdate

logger = logging.getLogger(__name__)


class BatchOperationManager:
    """批量操作管理器"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.template_manager = TemplateManager(db_session)
        self.version_manager = VersionManager(db_session)
        self.dependency_manager = DependencyManager(db_session)

    async def batch_create(
        self,
        configs: List[ConfigCreate],
        user_id: int,
        template_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """批量创建配置"""
        results = {"success": [], "failed": []}

        try:
            async with self.db.begin():
                for config in configs:
                    try:
                        # 如果指定了模板，验证配置
                        if template_name:
                            errors = await self.template_manager.validate_config(
                                template_name, config.dict()
                            )
                            if errors:
                                results["failed"].append(
                                    {"config": config.dict(), "error": errors}
                                )
                                continue

                        # 创建配置
                        new_config = await self._create_single_config(config, user_id)

                        results["success"].append(new_config)

                    except Exception as e:
                        results["failed"].append(
                            {"config": config.dict(), "error": str(e)}
                        )

            return results

        except Exception as e:
            logger.error(f"批量创建配置失败: {str(e)}")
            await self.db.rollback()
            raise

    async def batch_update(
        self, updates: List[ConfigUpdate], user_id: int, create_version: bool = True
    ) -> Dict[str, Any]:
        """批量更新配置"""
        results = {"success": [], "failed": []}

        try:
            async with self.db.begin():
                for update in updates:
                    try:
                        # 更新配置
                        updated_config = await self._update_single_config(
                            update, user_id, create_version
                        )

                        if updated_config:
                            results["success"].append(updated_config)
                        else:
                            results["failed"].append(
                                {"config": update.dict(), "error": "配置不存在"}
                            )

                    except Exception as e:
                        results["failed"].append(
                            {"config": update.dict(), "error": str(e)}
                        )

            return results

        except Exception as e:
            logger.error(f"批量更新配置失败: {str(e)}")
            await self.db.rollback()
            raise

    async def batch_delete(
        self, keys: List[str], user_id: int, force: bool = False
    ) -> Dict[str, Any]:
        """批量删除配置"""
        results = {"success": [], "failed": []}

        try:
            async with self.db.begin():
                for key in keys:
                    try:
                        # 检查依赖关系
                        if not force:
                            dependents = await self.dependency_manager.get_dependents(
                                key, recursive=True
                            )
                            if dependents:
                                results["failed"].append(
                                    {"key": key, "error": f"存在依赖项: {dependents}"}
                                )
                                continue

                        # 删除配置
                        success = await self._delete_single_config(key)

                        if success:
                            results["success"].append(key)
                        else:
                            results["failed"].append(
                                {"key": key, "error": "配置不存在"}
                            )

                    except Exception as e:
                        results["failed"].append({"key": key, "error": str(e)})

            return results

        except Exception as e:
            logger.error(f"批量删除配置失败: {str(e)}")
            await self.db.rollback()
            raise

    async def batch_validate(
        self, configs: List[Dict], template_name: str
    ) -> Dict[str, Any]:
        """批量验证配置"""
        results = {"valid": [], "invalid": []}

        try:
            for config in configs:
                errors = await self.template_manager.validate_config(
                    template_name, config
                )

                if errors:
                    results["invalid"].append({"config": config, "errors": errors})
                else:
                    results["valid"].append(config)

            return results

        except Exception as e:
            logger.error(f"批量验证配置失败: {str(e)}")
            raise

    async def _create_single_config(
        self, config: ConfigCreate, user_id: int
    ) -> Dict[str, Any]:
        """创建单个配置"""
        new_config = SystemConfig(
            key=config.key,
            value=config.value,
            description=config.description,
            created_by=user_id,
        )

        self.db.add(new_config)
        await self.db.flush()

        # 创建初始版本
        await self.version_manager.create_version(
            config.key,
            config.value,
            user_id,
            metadata=config.metadata,
            comment="初始版本",
        )

        return new_config

    async def _update_single_config(
        self, update: ConfigUpdate, user_id: int, create_version: bool
    ) -> Optional[Dict[str, Any]]:
        """更新单个配置"""
        config = await self.db.get(SystemConfig, update.key)
        if not config:
            return None

        # 更新配置
        for field, value in update.dict(exclude_unset=True).items():
            setattr(config, field, value)

        config.updated_by = user_id
        config.updated_at = datetime.utcnow()

        # 创建新版本
        if create_version:
            await self.version_manager.create_version(
                update.key,
                update.value,
                user_id,
                metadata=update.metadata,
                comment=update.comment,
            )

        return config

    async def _delete_single_config(self, key: str) -> bool:
        """删除单个配置"""
        result = await self.db.execute(
            update(SystemConfig).where(SystemConfig.key == key).values(is_active=False)
        )

        return result.rowcount > 0
