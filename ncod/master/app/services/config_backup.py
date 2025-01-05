"""
配置备份和恢复服务
"""

import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.backup import ConfigBackupHistory, ConfigRestoreHistory
from ..models.dependency import DependencyManager
from ..models.system import SystemConfig
from ..models.template import TemplateManager
from ..models.version import VersionManager

logger = logging.getLogger(__name__)


class BackupManager:
    """备份管理器"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.template_manager = TemplateManager(db_session)
        self.version_manager = VersionManager(db_session)
        self.dependency_manager = DependencyManager(db_session)
        self.backup_dir = Path(settings.BACKUP_DIR)

    async def create_backup(
        self,
        name: str,
        user_id: int,
        include_templates: bool = True,
        include_versions: bool = True,
        include_dependencies: bool = True,
    ) -> Dict[str, Any]:
        """创建备份"""
        try:
            # 确保备份目录存在
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # 备份配置数据
                configs = await self._backup_configs(temp_path)

                # 备份模板
                templates = []
                if include_templates:
                    templates = await self._backup_templates(temp_path)

                # 备份版本
                versions = []
                if include_versions:
                    versions = await self._backup_versions(temp_path)

                # 备份依赖关系
                dependencies = []
                if include_dependencies:
                    dependencies = await self._backup_dependencies(temp_path)

                # 创建备份元数据
                metadata = {
                    "name": name,
                    "created_at": datetime.utcnow().isoformat(),
                    "created_by": user_id,
                    "configs": len(configs),
                    "templates": len(templates),
                    "versions": len(versions),
                    "dependencies": len(dependencies),
                }

                # 写入元数据
                with open(temp_path / "metadata.json", "w") as f:
                    json.dump(metadata, f, indent=2)

                # 创建备份文件
                backup_file = self.backup_dir / f"{name}_{metadata['created_at']}.zip"
                shutil.make_archive(str(backup_file.with_suffix("")), "zip", temp_dir)

                # 记录备份历史
                await self._record_backup_history(
                    name, backup_file.name, metadata, user_id
                )

                return metadata

        except Exception as e:
            logger.error(f"创建备份失败: {str(e)}")
            raise

    async def restore_backup(
        self,
        backup_file: str,
        user_id: int,
        include_templates: bool = True,
        include_versions: bool = True,
        include_dependencies: bool = True,
    ) -> Dict[str, Any]:
        """恢复备份"""
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # 解压备份文件
                shutil.unpack_archive(
                    str(self.backup_dir / backup_file), temp_dir, "zip"
                )

                # 读取元数据
                with open(temp_path / "metadata.json") as f:
                    metadata = json.load(f)

                results = {
                    "configs": [],
                    "templates": [],
                    "versions": [],
                    "dependencies": [],
                }

                # 恢复配置数据
                results["configs"] = await self._restore_configs(temp_path, user_id)

                # 恢复模板
                if include_templates:
                    results["templates"] = await self._restore_templates(
                        temp_path, user_id
                    )

                # 恢复版本
                if include_versions:
                    results["versions"] = await self._restore_versions(
                        temp_path, user_id
                    )

                # 恢复依赖关系
                if include_dependencies:
                    results["dependencies"] = await self._restore_dependencies(
                        temp_path, user_id
                    )

                # 记录恢复历史
                await self._record_restore_history(backup_file, results, user_id)

                return results

        except Exception as e:
            logger.error(f"恢复备份失败: {str(e)}")
            raise

    async def list_backups(self) -> List[Dict[str, Any]]:
        """获取备份列表"""
        try:
            backups = []

            for file in self.backup_dir.glob("*.zip"):
                try:
                    # 创建临时目录
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # 解压元数据
                        shutil.unpack_archive(str(file), temp_dir, "zip")

                        # 读取元数据
                        with open(Path(temp_dir) / "metadata.json") as f:
                            metadata = json.load(f)

                        backups.append(
                            {"file": file.name, "size": file.stat().st_size, **metadata}
                        )

                except Exception as e:
                    logger.error(f"读取备份元数据失败: {str(e)}")

            return sorted(backups, key=lambda x: x["created_at"], reverse=True)

        except Exception as e:
            logger.error(f"获取备份列表失败: {str(e)}")
            raise

    async def delete_backup(self, backup_file: str) -> bool:
        """删除备份"""
        try:
            file = self.backup_dir / backup_file
            if file.exists():
                file.unlink()
                return True
            return False

        except Exception as e:
            logger.error(f"删除备份失败: {str(e)}")
            raise

    async def _backup_configs(self, temp_path: Path) -> List[Dict[str, Any]]:
        """备份配置数据"""
        query = select(SystemConfig).where(SystemConfig.is_active == True)
        result = await self.db.execute(query)
        configs = result.scalars().all()

        data = [
            {
                "key": c.key,
                "value": c.value,
                "description": c.description,
                "created_at": c.created_at.isoformat(),
                "created_by": c.created_by,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "updated_by": c.updated_by,
            }
            for c in configs
        ]

        with open(temp_path / "configs.json", "w") as f:
            json.dump(data, f, indent=2)

        return data

    async def _backup_templates(self, temp_path: Path) -> List[Dict[str, Any]]:
        """备份模板"""
        templates = await self.template_manager.list_templates()

        data = [
            {
                "name": t.name,
                "description": t.description,
                "schema": t.schema,
                "defaults": t.defaults,
                "validation": t.validation,
                "created_at": t.created_at.isoformat(),
                "created_by": t.created_by,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                "updated_by": t.updated_by,
            }
            for t in templates
        ]

        with open(temp_path / "templates.json", "w") as f:
            json.dump(data, f, indent=2)

        return data

    async def _backup_versions(self, temp_path: Path) -> List[Dict[str, Any]]:
        """备份版本"""
        query = select(ConfigVersion)
        result = await self.db.execute(query)
        versions = result.scalars().all()

        data = [
            {
                "config_key": v.config_key,
                "version": v.version,
                "value": v.value,
                "metadata": v.metadata,
                "comment": v.comment,
                "is_active": v.is_active,
                "created_at": v.created_at.isoformat(),
                "created_by": v.created_by,
            }
            for v in versions
        ]

        with open(temp_path / "versions.json", "w") as f:
            json.dump(data, f, indent=2)

        return data

    async def _backup_dependencies(self, temp_path: Path) -> List[Dict[str, Any]]:
        """备份依赖关系"""
        query = select(ConfigDependency)
        result = await self.db.execute(query)
        dependencies = result.scalars().all()

        data = [
            {
                "config_key": d.config_key,
                "depends_on": d.depends_on,
                "created_at": d.created_at.isoformat(),
                "created_by": d.created_by,
            }
            for d in dependencies
        ]

        with open(temp_path / "dependencies.json", "w") as f:
            json.dump(data, f, indent=2)

        return data

    async def _restore_configs(self, temp_path: Path, user_id: int) -> List[str]:
        """恢复配置数据"""
        with open(temp_path / "configs.json") as f:
            configs = json.load(f)

        restored = []

        for config in configs:
            try:
                # 创建或更新配置
                db_config = await self.db.get(SystemConfig, config["key"])
                if not db_config:
                    db_config = SystemConfig(
                        key=config["key"],
                        value=config["value"],
                        description=config["description"],
                        created_by=user_id,
                    )
                    self.db.add(db_config)
                else:
                    db_config.value = config["value"]
                    db_config.description = config["description"]
                    db_config.updated_by = user_id
                    db_config.updated_at = datetime.utcnow()

                restored.append(config["key"])

            except Exception as e:
                logger.error(f"恢复配置失败: {str(e)}")

        await self.db.commit()
        return restored

    async def _restore_templates(self, temp_path: Path, user_id: int) -> List[str]:
        """恢复模板"""
        with open(temp_path / "templates.json") as f:
            templates = json.load(f)

        restored = []

        for template in templates:
            try:
                await self.template_manager.create_template(
                    name=template["name"],
                    schema=template["schema"],
                    user_id=user_id,
                    description=template["description"],
                    defaults=template["defaults"],
                    validation=template["validation"],
                )
                restored.append(template["name"])

            except Exception as e:
                logger.error(f"恢复模板失败: {str(e)}")

        return restored

    async def _restore_versions(self, temp_path: Path, user_id: int) -> List[str]:
        """恢复版本"""
        with open(temp_path / "versions.json") as f:
            versions = json.load(f)

        restored = []

        for version in versions:
            try:
                await self.version_manager.create_version(
                    config_key=version["config_key"],
                    value=version["value"],
                    user_id=user_id,
                    metadata=version["metadata"],
                    comment=version["comment"],
                    activate=version["is_active"],
                )
                restored.append(f"{version['config_key']}@{version['version']}")

            except Exception as e:
                logger.error(f"恢复版本失败: {str(e)}")

        return restored

    async def _restore_dependencies(self, temp_path: Path, user_id: int) -> List[str]:
        """恢复依赖关系"""
        with open(temp_path / "dependencies.json") as f:
            dependencies = json.load(f)

        restored = []

        for dependency in dependencies:
            try:
                await self.dependency_manager.add_dependency(
                    config_key=dependency["config_key"],
                    depends_on=dependency["depends_on"],
                    user_id=user_id,
                )
                restored.append(
                    f"{dependency['config_key']}->{dependency['depends_on']}"
                )

            except Exception as e:
                logger.error(f"恢复依赖关系失败: {str(e)}")

        return restored

    async def _record_backup_history(
        self, name: str, file: str, metadata: Dict[str, Any], user_id: int
    ):
        """记录备份历史"""
        history = ConfigBackupHistory(
            name=name, file=file, metadata=metadata, backup_by=user_id
        )

        self.db.add(history)
        await self.db.commit()

    async def _record_restore_history(
        self, backup_file: str, results: Dict[str, Any], user_id: int
    ):
        """记录恢复历史"""
        history = ConfigRestoreHistory(
            backup_file=backup_file, results=results, restore_by=user_id
        )

        self.db.add(history)
        await self.db.commit()
