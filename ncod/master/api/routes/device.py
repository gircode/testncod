"""设备管理路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ncod.core.deps import (
    get_current_user,
    get_current_active_admin,
    get_permission_checker,
)
from ncod.core.logger import setup_logger
from ncod.master.models.user import User
from ncod.master.services.device import DeviceService
from ncod.master.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceUsageLog,
)

router = APIRouter()
device_service = DeviceService()
logger = setup_logger("device_routes")

# 创建权限检查器
device_permission = get_permission_checker("device")


@router.get(
    "/",
    response_model=List[DeviceResponse],
    dependencies=[Depends(device_permission("view"))],
)
async def get_devices(
    current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 100
):
    """获取设备列表"""
    try:
        return await device_service.get_devices(
            organization_id=current_user.organization_id, skip=skip, limit=limit
        )
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get devices",
        )


@router.post(
    "/",
    response_model=DeviceResponse,
    dependencies=[Depends(device_permission("manage"))],
)
async def create_device(
    device: DeviceCreate, current_user: User = Depends(get_current_active_admin)
):
    """创建设备"""
    try:
        return await device_service.create_device(device)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create device",
        )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str, current_user: User = Depends(get_current_user)):
    """获取设备详情"""
    device = await device_service.get_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )
    if device.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this device",
        )
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_update: DeviceUpdate,
    current_user: User = Depends(get_current_active_admin),
):
    """更新设备"""
    try:
        device = await device_service.update_device(device_id, device_update)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
            )
        return device
    except Exception as e:
        logger.error(f"Error updating device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device",
        )


@router.get("/{device_id}/usage", response_model=List[DeviceUsageLog])
async def get_device_usage(
    device_id: str,
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """获取设备使用记录"""
    try:
        logs = await device_service.get_device_usage_logs(
            device_id=device_id, skip=skip, limit=limit
        )
        return logs
    except Exception as e:
        logger.error(f"Error getting device usage logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device usage logs",
        )
