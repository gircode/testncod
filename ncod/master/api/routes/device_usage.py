"""设备使用记录路由"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from ncod.core.deps import (
    get_current_user,
    get_current_active_admin,
    get_permission_checker,
)
from ncod.core.logger import setup_logger
from ncod.master.models.user import User
from ncod.master.services.device_usage import DeviceUsageService
from ncod.master.schemas.device_usage import (
    DeviceUsageCreate,
    DeviceUsageUpdate,
    DeviceUsageResponse,
)

router = APIRouter()
device_usage_service = DeviceUsageService()
logger = setup_logger("device_usage_routes")

# 创建权限检查器
device_usage_permission = get_permission_checker("device_usage")


@router.get(
    "/",
    response_model=List[DeviceUsageResponse],
    dependencies=[Depends(device_usage_permission("view"))],
)
async def get_device_usage_logs(
    current_user: User = Depends(get_current_user),
    device_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    """获取设备使用记录列表"""
    try:
        return await device_usage_service.get_device_usage_logs(
            device_id=device_id, user_id=current_user.id, skip=skip, limit=limit
        )
    except Exception as e:
        logger.error(f"Error getting device usage logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device usage logs",
        )


@router.post(
    "/",
    response_model=DeviceUsageResponse,
    dependencies=[Depends(device_usage_permission("create"))],
)
async def create_device_usage(
    usage_data: DeviceUsageCreate, current_user: User = Depends(get_current_user)
):
    """创建设备使用记录"""
    try:
        return await device_usage_service.create_device_usage(
            user_id=current_user.id, usage_data=usage_data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating device usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create device usage",
        )


@router.get(
    "/{usage_id}",
    response_model=DeviceUsageResponse,
    dependencies=[Depends(device_usage_permission("view"))],
)
async def get_device_usage(
    usage_id: str, current_user: User = Depends(get_current_user)
):
    """获取设备使用记录详情"""
    usage = await device_usage_service.get_device_usage(usage_id)
    if not usage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device usage not found"
        )
    if usage.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this device usage",
        )
    return usage


@router.put(
    "/{usage_id}",
    response_model=DeviceUsageResponse,
    dependencies=[Depends(device_usage_permission("update"))],
)
async def update_device_usage(
    usage_id: str,
    usage_update: DeviceUsageUpdate,
    current_user: User = Depends(get_current_user),
):
    """更新设备使用记录"""
    try:
        # 获取使用记录
        usage = await device_usage_service.get_device_usage(usage_id)
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device usage not found"
            )

        # 检查权限
        if usage.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this device usage",
            )

        # 更新记录
        updated_usage = await device_usage_service.update_device_usage(
            usage_id, usage_update
        )
        if not updated_usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device usage not found"
            )
        return updated_usage
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating device usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device usage",
        )


@router.post(
    "/{usage_id}/end",
    response_model=DeviceUsageResponse,
    dependencies=[Depends(device_usage_permission("update"))],
)
async def end_device_usage(
    usage_id: str, current_user: User = Depends(get_current_user)
):
    """结束设备使用"""
    try:
        # 获取使用记录
        usage = await device_usage_service.get_device_usage(usage_id)
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device usage not found"
            )

        # 检查权限
        if usage.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to end this device usage",
            )

        # 结束使用
        ended_usage = await device_usage_service.end_device_usage(usage_id)
        if not ended_usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device usage not found"
            )
        return ended_usage
    except Exception as e:
        logger.error(f"Error ending device usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end device usage",
        )
