"""
设备管理API路由
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from ncod.master.app.db.session import get_db
from ncod.master.app.deps import get_current_admin_user, get_current_user
from ncod.master.app.models.auth import User
from ncod.master.app.models.device import Device, DevicePermission, DeviceReservation
from ncod.master.app.services.device import DeviceService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/list")
async def list_devices(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Device]:
    """获取可用设备列表"""
    device_service = DeviceService(db)
    return await device_service.get_available_devices(
        user=current_user, skip=skip, limit=limit
    )


@router.get("/{device_id}")
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Device:
    """获取设备详情"""
    device_service = DeviceService(db)
    return await device_service.get_device(device_id)


@router.post("/{device_id}/connect")
async def connect_device(
    device_id: int,
    client_ip: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    """连接设备"""
    device_service = DeviceService(db)
    return await device_service.connect_device(
        device_id=device_id, user=current_user, client_ip=client_ip
    )


@router.post("/{device_id}/disconnect")
async def disconnect_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    """断开设备连接"""
    device_service = DeviceService(db)
    return await device_service.disconnect_device(
        device_id=device_id, user=current_user
    )


@router.post("/{device_id}/grant")
async def grant_permission(
    device_id: int,
    user_id: int,
    permission_type: str = "read",
    is_temporary: bool = False,
    valid_days: int | None = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> DevicePermission:
    """授予设备使用权限"""
    device_service = DeviceService(db)
    return await device_service.grant_permission(
        device_id=device_id,
        user_id=user_id,
        granted_by=current_admin,
        permission_type=permission_type,
        is_temporary=is_temporary,
        valid_days=valid_days,
    )


@router.post("/permission/{permission_id}/revoke")
async def revoke_permission(
    permission_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    """撤销设备使用权限"""
    device_service = DeviceService(db)
    return await device_service.revoke_permission(
        permission_id=permission_id, admin=current_admin
    )


@router.post("/{device_id}/reserve")
async def create_reservation(
    device_id: int,
    start_time: datetime,
    end_time: datetime,
    remarks: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeviceReservation:
    """创建设备预约"""
    device_service = DeviceService(db)
    return await device_service.create_reservation(
        device_id=device_id,
        user=current_user,
        start_time=start_time,
        end_time=end_time,
        remarks=remarks,
    )


@router.post("/reservation/{reservation_id}/handle")
async def handle_reservation(
    reservation_id: int,
    approve: bool,
    remarks: str | None = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> DeviceReservation:
    """处理设备预约"""
    device_service = DeviceService(db)
    return await device_service.handle_reservation(
        reservation_id=reservation_id,
        admin=current_admin,
        approve=approve,
        remarks=remarks,
    )


@router.post("/sync")
async def sync_devices(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> List[Device]:
    """同步设备列表"""
    device_service = DeviceService(db)
    return await device_service.sync_devices()
