"""设备相关API端点"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.db.base import get_db
from ....core.services.device import DeviceService
from ....middleware.auth import get_current_user
from ....models.user import User
from ....models.device import Device
from ....schemas.device import DeviceCreate, DeviceUpdate, DeviceStatus
from ....utils.logger import logger

router = APIRouter()
device_service = DeviceService()


@router.get("/", response_model=List[Device])
async def get_devices(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> List[Device]:
    """获取设备列表"""
    try:
        return await device_service.get_user_devices(db, current_user.id)
    except Exception as e:
        logger.error("获取设备列表失败", exc_info=True)
        raise


@router.post("/", response_model=Device)
async def create_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Device:
    """创建设备"""
    try:
        device_data.owner_id = current_user.id
        return await device_service.create_device(db, device_data)
    except Exception as e:
        logger.error("创建设备失败", exc_info=True)
        raise


@router.get("/{device_id}", response_model=Device)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Device:
    """获取设备详情"""
    try:
        device = await device_service.get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在"
            )
        if device.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此设备"
            )
        return device
    except Exception as e:
        logger.error("获取设备详情失败", exc_info=True)
        raise


@router.put("/{device_id}", response_model=Device)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Device:
    """更新设备"""
    try:
        device = await device_service.get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在"
            )
        if device.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权修改此设备"
            )
        return await device_service.update_device(db, device_id, device_data)
    except Exception as e:
        logger.error("更新设备失败", exc_info=True)
        raise
