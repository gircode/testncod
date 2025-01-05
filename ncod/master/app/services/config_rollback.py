"""
配置回滚服务
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit import ConfigAudit
from ..models.dependency import DependencyManager
from ..models.system import SystemConfig
from ..models.version import VersionManager
from ..services.config_audit import AuditManager

logger = logging.getLogger(__name__)


class RollbackManager:
    """回滚管理器"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.version_manager = VersionManager(db_session)
        self.dependency_manager = DependencyManager(db_session)
        self.audit_manager = AuditManager(db_session)

    async def rollback_to_version(
        self, config_key: str, version: int, user_id: int, force: bool = False
    ) -> Dict[str, Any]:
        """回滚到指定版本"""
        try:
            # 获取目标版本
            target_version = await self.version_manager.get_version(config_key, version)
            if not target_version:
                raise ValueError(f"版本不存在: {version}")

            # 获取当前版本
            current_version = await self.version_manager.get_version(config_key)
            if not current_version:
                raise ValueError(f"配置不存在: {config_key}")

            # 检查依赖
            if not force:
                dependents = await self.dependency_manager.get_dependents(
                    config_key, recursive=True
                )
                if dependents:
                    raise ValueError(f"存在依赖项: {dependents}")

            # 执行回滚
            async with self.db.begin():
                # 更新配置值
                config = await self.db.get(SystemConfig, config_key)
                old_value = config.value
                config.value = target_version.value
                config.updated_by = user_id
                config.updated_at = datetime.utcnow()

                # 创建新版本
                new_version = await self.version_manager.create_version(
                    config_key,
                    target_version.value,
                    user_id,
                    metadata=target_version.metadata,
                    comment=f"回滚到版本 {version}",
                )

                # 记录审计
                await self.audit_manager.record_operation(
                    config_key=config_key,
                    operation="rollback",
                    user_id=user_id,
                    old_value=old_value,
                    new_value=target_version.value,
                    metadata={
                        "from_version": current_version.version,
                        "to_version": version,
                    },
                )

            return {
                "success": True,
                "config_key": config_key,
                "from_version": current_version.version,
                "to_version": version,
                "new_version": new_version.version,
            }

        except Exception as e:
            logger.error(f"回滚配置失败: {str(e)}")
            raise

    async def rollback_multiple(
        self, rollbacks: List[Dict[str, Any]], user_id: int, force: bool = False
    ) -> Dict[str, Any]:
        """批量回滚配置"""
        results = {"success": [], "failed": []}

        try:
            for rollback in rollbacks:
                try:
                    result = await self.rollback_to_version(
                        config_key=rollback["config_key"],
                        version=rollback["version"],
                        user_id=user_id,
                        force=force,
                    )
                    results["success"].append(result)

                except Exception as e:
                    results["failed"].append(
                        {
                            "config_key": rollback["config_key"],
                            "version": rollback["version"],
                            "error": str(e),
                        }
                    )

            return results

        except Exception as e:
            logger.error(f"批量回滚配置失败: {str(e)}")
            raise

    async def rollback_to_time(
        self, config_key: str, target_time: datetime, user_id: int, force: bool = False
    ) -> Dict[str, Any]:
        """回滚到指定时间点"""
        try:
            # 获取目标时间点的版本
            versions = await self.version_manager.list_versions(config_key)
            target_version = None

            for version in versions:
                if version.created_at <= target_time:
                    target_version = version
                    break

            if not target_version:
                raise ValueError(f"未找到{target_time}之前的版本")

            # 执行回滚
            return await self.rollback_to_version(
                config_key, target_version.version, user_id, force
            )

        except Exception as e:
            logger.error(f"回滚配置失败: {str(e)}")
            raise

    async def get_rollback_preview(
        self, config_key: str, version: int
    ) -> Dict[str, Any]:
        """获取回滚预览"""
        try:
            # 获取目标版本
            target_version = await self.version_manager.get_version(config_key, version)
            if not target_version:
                raise ValueError(f"版本不存在: {version}")

            # 获取当前版本
            current_version = await self.version_manager.get_version(config_key)
            if not current_version:
                raise ValueError(f"配置不存在: {config_key}")

            # 获取依赖项
            dependents = await self.dependency_manager.get_dependents(
                config_key, recursive=True
            )

            # 比较差异
            diff = await self.version_manager.compare_versions(
                config_key, current_version.version, version
            )

            return {
                "config_key": config_key,
                "current_version": current_version.version,
                "target_version": version,
                "dependents": dependents,
                "diff": diff,
            }

        except Exception as e:
            logger.error(f"获取回滚预览失败: {str(e)}")
            raise

    async def get_rollback_history(
        self, config_key: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取回滚历史"""
        try:
            query = select(ConfigAudit).where(ConfigAudit.operation == "rollback")

            if config_key:
                query = query.where(ConfigAudit.config_key == config_key)

            query = (
                query.order_by(ConfigAudit.created_at.desc()).offset(skip).limit(limit)
            )

            result = await self.db.execute(query)
            audits = result.scalars().all()

            return [
                {
                    "config_key": audit.config_key,
                    "from_version": audit.metadata["from_version"],
                    "to_version": audit.metadata["to_version"],
                    "user_id": audit.user_id,
                    "created_at": audit.created_at,
                }
                for audit in audits
            ]

        except Exception as e:
            logger.error(f"获取回滚历史失败: {str(e)}")
            raise
