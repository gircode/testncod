"""
Data Synchronization Module
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from .config import SyncConfig
from .database import SlaveDatabase


class DataSynchronizer:
    def __init__(self, config: SyncConfig):
        self.config = config
        self.db = SlaveDatabase(config.database)
        self.current_sync: Optional[Dict] = None
        self.sync_history: List[Dict] = []

    async def start_sync(self, sync_config: Dict) -> Dict:
        """启动同步任务"""
        if self.current_sync:
            raise Exception("Sync already in progress")

        self.current_sync = {
            "id": str(datetime.utcnow().timestamp()),
            "start_time": datetime.utcnow(),
            "status": "running",
            "config": sync_config,
            "progress": 0,
            "errors": [],
        }

        asyncio.create_task(self._run_sync())
        return self.current_sync

    async def _run_sync(self):
        """执行同步任务"""
        try:
            for sync_type in self.config.sync_types:
                if sync_type not in self.current_sync["config"]["types"]:
                    continue

                await self._sync_data_type(sync_type)
                self.current_sync["progress"] += 100 / len(self.config.sync_types)

            self.current_sync["status"] = "completed"
            self.current_sync["end_time"] = datetime.utcnow()

        except Exception as e:
            logging.error(f"Sync error: {e}")
            self.current_sync["status"] = "failed"
            self.current_sync["errors"].append(str(e))
            self.current_sync["end_time"] = datetime.utcnow()

        finally:
            self.sync_history.append(self.current_sync)
            if len(self.sync_history) > 100:
                self.sync_history = self.sync_history[-100:]
            self.current_sync = None

    async def _sync_data_type(self, sync_type: str):
        """同步特定类型的数据"""
        offset = 0
        while True:
            try:
                # 获取主服务器数据
                data = await self._fetch_from_master(
                    sync_type, offset, self.config.batch_size
                )

                if not data:
                    break

                # 更新本地数据
                await self._update_local_data(sync_type, data)

                offset += len(data)

            except Exception as e:
                for attempt in range(self.config.retry_attempts):
                    try:
                        await asyncio.sleep(self.config.retry_delay)
                        # 重试同步
                        data = await self._fetch_from_master(
                            sync_type, offset, self.config.batch_size
                        )
                        if data:
                            await self._update_local_data(sync_type, data)
                            offset += len(data)
                            break
                    except Exception as retry_e:
                        if attempt == self.config.retry_attempts - 1:
                            raise retry_e

    async def _fetch_from_master(
        self, sync_type: str, offset: int, limit: int
    ) -> List[Dict]:
        """从主服务器获取数据"""
        # 实现从主服务器获取数据的逻辑
        # 这里需要与主服务器API集成
        pass

    async def _update_local_data(self, sync_type: str, data: List[Dict]):
        """更新本地数据"""
        if sync_type == "device_data":
            await self._sync_device_data(data)
        elif sync_type == "user_data":
            await self._sync_user_data(data)
        elif sync_type == "settings":
            await self._sync_settings(data)

    async def _sync_device_data(self, data: List[Dict]):
        """同步设备数据"""
        async with self.db.transaction() as conn:
            for device in data:
                await conn.execute(
                    """
                    INSERT INTO devices (id, name, status, config)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE
                    SET name = $2, status = $3, config = $4
                """,
                    device["id"],
                    device["name"],
                    device["status"],
                    device["config"],
                )

    async def _sync_user_data(self, data: List[Dict]):
        """同步用户数据"""
        async with self.db.transaction() as conn:
            for user in data:
                await conn.execute(
                    """
                    INSERT INTO users (id, username, role, permissions)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE
                    SET username = $2, role = $3, permissions = $4
                """,
                    user["id"],
                    user["username"],
                    user["role"],
                    user["permissions"],
                )

    async def _sync_settings(self, data: List[Dict]):
        """同步设置数据"""
        async with self.db.transaction() as conn:
            for setting in data:
                await conn.execute(
                    """
                    INSERT INTO settings (key, value, updated_at)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (key) DO UPDATE
                    SET value = $2, updated_at = $3
                """,
                    setting["key"],
                    setting["value"],
                    setting["updated_at"],
                )

    async def get_status(self) -> Dict:
        """获取同步状态"""
        return {
            "current_sync": self.current_sync,
            "last_sync": self.sync_history[-1] if self.sync_history else None,
            "total_syncs": len(self.sync_history),
            "failed_syncs": sum(
                1 for sync in self.sync_history if sync["status"] == "failed"
            ),
        }
