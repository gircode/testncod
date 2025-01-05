"""配置同步服务"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.sync import ConfigSyncHistory
from ..models.system import SystemConfig
from ..models.version import VersionManager
from ..schemas.config import ConfigSync

logger = logging.getLogger(__name__)


class SyncManager:
    """同步管理器"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.version_manager = VersionManager(db_session)
        self._sync_lock = asyncio.Lock()

    async def sync_to_slave(
        self, slave_url: str, configs: List[str], user_id: int
    ) -> Dict[str, Any]:
        """同步配置到从节点"""
        results = {"success": [], "failed": []}

        try:
            async with self._sync_lock:
                # 获取配置数据
                config_data = await self._get_config_data(configs)

                # 发送同步请求
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{slave_url}/api/v1/config/sync", json=config_data
                    ) as response:
                        if response.status == 200:
                            results["success"] = configs
                        else:
                            error = await response.text()
                            results["failed"].append(
                                {"configs": configs, "error": error}
                            )

                # 记录同步历史
                await self._record_sync_history(slave_url, configs, results, user_id)

            return results

        except Exception as e:
            logger.error(f"同步配置失败: {str(e)}")
            raise

    async def sync_from_master(
        self, config_data: Dict[str, Any], user_id: int
    ) -> Dict[str, Any]:
        """从主节点同步配置"""
        results = {"success": [], "failed": []}

        try:
            async with self._sync_lock:
                for key, data in config_data.items():
                    try:
                        # 更新配置
                        await self._update_config(key, data, user_id)
                        results["success"].append(key)

                    except Exception as e:
                        results["failed"].append({"key": key, "error": str(e)})

                # 记录同步历史
                await self._record_sync_history(
                    "master", list(config_data.keys()), results, user_id
                )

            return results

        except Exception as e:
            logger.error(f"从主节点同步配置失败: {str(e)}")
            raise

    async def get_sync_status(self, slave_url: Optional[str] = None) -> Dict[str, Any]:
        """获取同步状态"""
        try:
            query = select(ConfigSyncHistory)

            if slave_url:
                query = query.where(ConfigSyncHistory.target == slave_url)

            query = query.order_by(ConfigSyncHistory.sync_at.desc()).limit(100)

            result = await self.db.execute(query)
            history = result.scalars().all()

            return {
                "total_syncs": len(history),
                "last_sync": history[0].sync_at if history else None,
                "history": [
                    {
                        "target": h.target,
                        "configs": h.configs,
                        "status": h.status,
                        "sync_at": h.sync_at,
                        "sync_by": h.sync_by,
                    }
                    for h in history
                ],
            }

        except Exception as e:
            logger.error(f"获取同步状态失败: {str(e)}")
            raise

    async def _get_config_data(self, configs: List[str]) -> Dict[str, Any]:
        """获取配置数据"""
        data = {}

        for key in configs:
            # 获取当前活动版本
            version = await self.version_manager.get_version(key)
            if version:
                data[key] = {
                    "value": version.value,
                    "metadata": version.metadata,
                    "version": version.version,
                }

        return data

    async def _update_config(self, key: str, data: Dict[str, Any], user_id: int):
        """更新配置"""
        # 检查版本
        current = await self.version_manager.get_version(key)
        if current and current.version >= data["version"]:
            return

        # 更新配置
        config = await self.db.get(SystemConfig, key)
        if not config:
            config = SystemConfig(key=key, value=data["value"], created_by=user_id)
            self.db.add(config)
        else:
            config.value = data["value"]
            config.updated_by = user_id
            config.updated_at = datetime.utcnow()

        # 创建新版本
        await self.version_manager.create_version(
            key,
            data["value"],
            user_id,
            metadata=data.get("metadata"),
            comment="从主节点同步",
        )

    async def _record_sync_history(
        self, target: str, configs: List[str], results: Dict[str, Any], user_id: int
    ):
        """记录同步历史"""
        history = ConfigSyncHistory(
            target=target, configs=configs, status=json.dumps(results), sync_by=user_id
        )

        self.db.add(history)
        await self.db.commit()
