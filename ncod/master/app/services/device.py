"""
设备管理服务
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.auth import Group, User
from ..models.device import (
    Device,
    DeviceGroup,
    DevicePermission,
    DeviceReservation,
    DeviceUsageLog,
)
from .virtualhere import VirtualHereService

# 配置日志
logger = logging.getLogger(__name__)


class DeviceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vh_service = VirtualHereService()

    async def sync_devices(self) -> List[Device]:
        """同步VirtualHere设备列表"""
        try:
            # 获取VirtualHere设备列表
            vh_devices = await self.vh_service.list_devices()

            # 获取现有设备列表
            result = await self.db.execute(select(Device))
            existing_devices = {d.device_id: d for d in result.scalars().all()}

            # 更新或创建设备
            for vh_device in vh_devices:
                device_id = vh_device["id"]
                if device_id in existing_devices:
                    # 更新现有设备
                    device = existing_devices[device_id]
                    device.name = vh_device["name"]
                    device.type = vh_device["type"]
                    device.is_available = vh_device["available"]
                    device.last_seen = datetime.utcnow()
                    device.metadata = vh_device
                else:
                    # 创建新设备
                    device = Device(
                        device_id=device_id,
                        name=vh_device["name"],
                        type=vh_device["type"],
                        is_available=vh_device["available"],
                        last_seen=datetime.utcnow(),
                        metadata=vh_device,
                    )
                    self.db.add(device)

            # 标记离线设备
            offline_threshold = datetime.utcnow() - timedelta(
                seconds=settings.DEVICE_OFFLINE_TIMEOUT
            )
            await self.db.execute(
                select(Device)
                .where(Device.last_seen < offline_threshold)
                .update({"is_available": False})
            )

            await self.db.commit()

            # 返回更新后的设备列表
            result = await self.db.execute(select(Device))
            return result.scalars().all()

        except Exception as e:
            logger.error(f"同步设备失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="同步设备失败"
            )

    async def get_device(self, device_id: int) -> Device:
        """获取设备信息"""
        result = await self.db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在"
            )

        return device

    async def get_available_devices(
        self, user: User, skip: int = 0, limit: int = 100
    ) -> List[Device]:
        """获取用户可用的设备列表"""
        try:
            # 构建查询条件
            conditions = [Device.is_active == True, Device.is_available == True]

            # 如果不是管理员,只能看到有权限的设备
            if not user.is_admin:
                # 获取用户的权限
                permission_subquery = select(DevicePermission.device_id).where(
                    and_(
                        DevicePermission.user_id == user.id,
                        or_(
                            DevicePermission.valid_until > datetime.utcnow(),
                            DevicePermission.valid_until == None,
                        ),
                    )
                )

                # 获取用户组的设备
                group_subquery = (
                    select(Device.id)
                    .join(device_group)
                    .join(Group)
                    .where(Group.id == user.group_id)
                )

                conditions.append(
                    or_(
                        Device.id.in_(permission_subquery),
                        Device.id.in_(group_subquery),
                    )
                )

            # 执行查询
            result = await self.db.execute(
                select(Device).where(and_(*conditions)).offset(skip).limit(limit)
            )

            return result.scalars().all()

        except Exception as e:
            logger.error(f"获取可用设备列表失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取可用设备列表失败",
            )

    async def connect_device(self, device_id: int, user: User, client_ip: str) -> bool:
        """连接设备"""
        try:
            # 获取设备
            device = await self.get_device(device_id)

            # 检查设备是否可用
            if not device.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="设备不可用"
                )

            # 检查设备是否被占用
            if device.current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="设备已被占用"
                )

            # 检查用户权限
            if not user.is_admin:
                result = await self.db.execute(
                    select(DevicePermission).where(
                        and_(
                            DevicePermission.device_id == device_id,
                            DevicePermission.user_id == user.id,
                            or_(
                                DevicePermission.valid_until > datetime.utcnow(),
                                DevicePermission.valid_until == None,
                            ),
                        )
                    )
                )
                permission = result.scalar_one_or_none()

                if not permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="没有设备使用权限"
                    )

            # 连接设备
            success = await self.vh_service.connect_device(
                device.device_id, str(user.id), client_ip
            )

            if success:
                # 更新设备状态
                device.current_user_id = user.id

                # 记录使用日志
                log = DeviceUsageLog(
                    device_id=device_id,
                    user_id=user.id,
                    action="connect",
                    client_ip=client_ip,
                    status="success",
                )
                self.db.add(log)

                await self.db.commit()
                return True

            return False

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"连接设备失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="连接设备失败"
            )

    async def disconnect_device(self, device_id: int, user: User) -> bool:
        """断开设备连接"""
        try:
            # 获取设备
            device = await self.get_device(device_id)

            # 检查是否是当前用户的设备
            if device.current_user_id != user.id and not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="无权断开此设备"
                )

            # 断开设备连接
            success = await self.vh_service.disconnect_device(device.device_id)

            if success:
                # 更新设备状态
                device.current_user_id = None

                # 更新使用日志
                result = await self.db.execute(
                    select(DeviceUsageLog).where(
                        and_(
                            DeviceUsageLog.device_id == device_id,
                            DeviceUsageLog.user_id == user.id,
                            DeviceUsageLog.end_time == None,
                        )
                    )
                )
                log = result.scalar_one_or_none()

                if log:
                    log.end_time = datetime.utcnow()
                    log.duration = int((log.end_time - log.start_time).total_seconds())

                await self.db.commit()
                return True

            return False

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"断开设备失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="断开设备失败"
            )

    async def grant_permission(
        self,
        device_id: int,
        user_id: int,
        granted_by: User,
        permission_type: str = "read",
        is_temporary: bool = False,
        valid_days: Optional[int] = None,
    ) -> DevicePermission:
        """授予设备使用权限"""
        try:
            # 检查设备是否存在
            device = await self.get_device(device_id)

            # 检查用户是否存在
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
                )

            # 检查授权者权限
            if not granted_by.is_admin:
                # 检查是否是同组或上级管理员
                if granted_by.group_id != user.group_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN, detail="无权授予权限"
                    )

            # 创建权限记录
            permission = DevicePermission(
                device_id=device_id,
                user_id=user_id,
                granted_by_id=granted_by.id,
                permission_type=permission_type,
                is_temporary=is_temporary,
            )

            if is_temporary and valid_days:
                permission.valid_until = datetime.utcnow() + timedelta(days=valid_days)

            self.db.add(permission)
            await self.db.commit()
            await self.db.refresh(permission)

            return permission

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"授予权限失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="授予权限失败"
            )

    async def revoke_permission(self, permission_id: int, admin: User) -> bool:
        """撤销设备使用权限"""
        try:
            # 获取权限记录
            result = await self.db.execute(
                select(DevicePermission).where(DevicePermission.id == permission_id)
            )
            permission = result.scalar_one_or_none()

            if not permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="权限记录不存在"
                )

            # 检查撤销者权限
            if not admin.is_admin and permission.granted_by_id != admin.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="无权撤销此权限"
                )

            # 删除权限记录
            await self.db.delete(permission)
            await self.db.commit()

            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"撤销权限失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="撤销权限失败"
            )

    async def create_reservation(
        self,
        device_id: int,
        user: User,
        start_time: datetime,
        end_time: datetime,
        remarks: Optional[str] = None,
    ) -> DeviceReservation:
        """创建设备预约"""
        try:
            # 检查设备是否存在
            device = await self.get_device(device_id)

            # 检查时间是否合法
            if start_time >= end_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="预约时间不合法"
                )

            # 检查是否有时间冲突
            result = await self.db.execute(
                select(DeviceReservation).where(
                    and_(
                        DeviceReservation.device_id == device_id,
                        DeviceReservation.status == "approved",
                        or_(
                            and_(
                                DeviceReservation.start_time <= start_time,
                                DeviceReservation.end_time > start_time,
                            ),
                            and_(
                                DeviceReservation.start_time < end_time,
                                DeviceReservation.end_time >= end_time,
                            ),
                        ),
                    )
                )
            )

            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="预约时间冲突"
                )

            # 创建预约记录
            reservation = DeviceReservation(
                device_id=device_id,
                user_id=user.id,
                start_time=start_time,
                end_time=end_time,
                status="pending",
                remarks=remarks,
            )

            self.db.add(reservation)
            await self.db.commit()
            await self.db.refresh(reservation)

            return reservation

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建预约失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建预约失败"
            )

    async def handle_reservation(
        self,
        reservation_id: int,
        admin: User,
        approve: bool,
        remarks: Optional[str] = None,
    ) -> DeviceReservation:
        """处理设备预约"""
        try:
            # 获取预约记录
            result = await self.db.execute(
                select(DeviceReservation).where(DeviceReservation.id == reservation_id)
            )
            reservation = result.scalar_one_or_none()

            if not reservation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="预约记录不存在"
                )

            # 更新预约状态
            reservation.status = "approved" if approve else "rejected"
            if remarks:
                reservation.remarks = remarks

            await self.db.commit()
            await self.db.refresh(reservation)

            return reservation

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"处理预约失败: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="处理预约失败"
            )
