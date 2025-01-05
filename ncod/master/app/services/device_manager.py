"""
设备管理服务
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..exceptions import DeviceError
from ..models.auth import Group, GroupRelation, User
from ..models.device import Device, DeviceGroup, DevicePermission

logger = logging.getLogger(__name__)


class DeviceManager:
    """设备管理器"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._device_locks: Dict[int, asyncio.Lock] = {}
        self._active_connections: Dict[str, Dict] = {}

    async def check_device_permission(
        self, user_id: int, device_id: int, action: str
    ) -> bool:
        """检查用户是否有设备操作权限"""
        try:
            # 获取用户信息
            user = await self.db.get(User, user_id)
            if not user:
                return False

            # 获取设备信息
            device = await self.db.get(Device, device_id)
            if not device:
                return False

            # 检查设备组权限
            query = select(DevicePermission).where(
                and_(
                    DevicePermission.group_id == user.group_id,
                    DevicePermission.device_group_id == device.group_id,
                    DevicePermission.action == action,
                )
            )
            result = await self.db.execute(query)
            permission = result.scalar_one_or_none()

            if permission:
                return True

            # 检查组间共享权限
            if action == "use":
                query = select(GroupRelation).where(
                    and_(
                        GroupRelation.group_id == device.group_id,
                        GroupRelation.related_group_id == user.group_id,
                        GroupRelation.allow_device_sharing == True,
                    )
                )
                result = await self.db.execute(query)
                relation = result.scalar_one_or_none()

                return relation is not None

            return False

        except Exception as e:
            logger.error(f"检查设备权限失败: {str(e)}")
            return False

    async def acquire_device(
        self, user_id: int, device_id: int, client_info: Dict
    ) -> bool:
        """尝试获取设备使用权"""
        if device_id not in self._device_locks:
            self._device_locks[device_id] = asyncio.Lock()

        async with self._device_locks[device_id]:
            try:
                # 检查权限
                if not await self.check_device_permission(user_id, device_id, "use"):
                    raise DeviceError("没有设备使用权限")

                # 检查设备状态
                device = await self.db.get(Device, device_id)
                if not device or not device.is_active:
                    raise DeviceError("设备不可用")

                # 检查是否已被占用
                connection_key = f"{device_id}"
                if connection_key in self._active_connections:
                    current_conn = self._active_connections[connection_key]
                    # 如果是同一用户的重连，允许
                    if current_conn["user_id"] == user_id:
                        current_conn.update(
                            {
                                "client_info": client_info,
                                "last_active": datetime.utcnow(),
                            }
                        )
                        return True
                    raise DeviceError("设备已被占用")

                # 记录连接信息
                self._active_connections[connection_key] = {
                    "user_id": user_id,
                    "client_info": client_info,
                    "connected_at": datetime.utcnow(),
                    "last_active": datetime.utcnow(),
                }

                # 更新设备状态
                device.current_user_id = user_id
                device.last_used = datetime.utcnow()
                await self.db.commit()

                return True

            except Exception as e:
                logger.error(f"获取设备使用权失败: {str(e)}")
                await self.db.rollback()
                return False

    async def release_device(
        self, user_id: int, device_id: int, force: bool = False
    ) -> bool:
        """释放设备"""
        if device_id not in self._device_locks:
            return False

        async with self._device_locks[device_id]:
            try:
                connection_key = f"{device_id}"
                if connection_key not in self._active_connections:
                    return True

                current_conn = self._active_connections[connection_key]
                if not force and current_conn["user_id"] != user_id:
                    # 检查是否有强制断开权限
                    if not await self.check_device_permission(
                        user_id, device_id, "force_disconnect"
                    ):
                        raise DeviceError("没有强制断开权限")

                # 更新设备状态
                device = await self.db.get(Device, device_id)
                if device:
                    device.current_user_id = None
                    await self.db.commit()

                # 移除连接记录
                del self._active_connections[connection_key]
                return True

            except Exception as e:
                logger.error(f"释放设备失败: {str(e)}")
                await self.db.rollback()
                return False

    async def get_available_devices(
        self, user_id: int, include_used: bool = False
    ) -> List[Device]:
        """获取用户可用的设备列表"""
        try:
            # 获取用户信息
            user = await self.db.get(User, user_id)
            if not user:
                return []

            # 获取用户组的设备权限
            query = (
                select(Device)
                .join(
                    DevicePermission,
                    and_(
                        DevicePermission.device_group_id == Device.group_id,
                        DevicePermission.group_id == user.group_id,
                        DevicePermission.action == "use",
                    ),
                )
                .where(Device.is_active == True)
            )

            if not include_used:
                query = query.where(Device.current_user_id.is_(None))

            # 获取可共享的设备
            shared_query = (
                select(Device)
                .join(
                    GroupRelation,
                    and_(
                        GroupRelation.group_id == Device.group_id,
                        GroupRelation.related_group_id == user.group_id,
                        GroupRelation.allow_device_sharing == True,
                    ),
                )
                .where(Device.is_active == True)
            )

            if not include_used:
                shared_query = shared_query.where(Device.current_user_id.is_(None))

            # 合并结果
            result = await self.db.execute(query)
            own_devices = result.scalars().all()

            result = await self.db.execute(shared_query)
            shared_devices = result.scalars().all()

            return list(set(own_devices) | set(shared_devices))

        except Exception as e:
            logger.error(f"获取可用设备失败: {str(e)}")
            return []

    async def get_device_status(self, device_id: int) -> Optional[Dict]:
        """获取设备状态"""
        try:
            device = await self.db.get(Device, device_id)
            if not device:
                return None

            status = {
                "id": device.id,
                "name": device.name,
                "type": device.type,
                "is_active": device.is_active,
                "group_id": device.group_id,
                "last_used": device.last_used,
                "current_user_id": device.current_user_id,
            }

            # 添加当前连接信息
            connection_key = f"{device_id}"
            if connection_key in self._active_connections:
                conn = self._active_connections[connection_key]
                status.update(
                    {
                        "connected_user_id": conn["user_id"],
                        "connected_at": conn["connected_at"],
                        "last_active": conn["last_active"],
                    }
                )

            return status

        except Exception as e:
            logger.error(f"获取设备状态失败: {str(e)}")
            return None

    async def cleanup_inactive_connections(self):
        """清理不活跃的连接"""
        try:
            current_time = datetime.utcnow()
            timeout = timedelta(seconds=settings.DEVICE_INACTIVE_TIMEOUT)

            inactive_connections = [
                (key, conn)
                for key, conn in self._active_connections.items()
                if current_time - conn["last_active"] > timeout
            ]

            for key, conn in inactive_connections:
                device_id = int(key)
                await self.release_device(conn["user_id"], device_id)

        except Exception as e:
            logger.error(f"清理不活跃连接失败: {str(e)}")

    async def start_cleanup_task(self):
        """启动清理任务"""
        while True:
            await self.cleanup_inactive_connections()
            await asyncio.sleep(settings.CLEANUP_INTERVAL)
