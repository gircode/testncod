"""设备相关API端点"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from ncod.core.auth import get_current_user
from ncod.core.device import DeviceService
from ncod.models.device import Device
from ncod.schemas.device import DeviceCreate, DeviceUpdate, DeviceInDB
from ncod.utils.logger import logger

router = APIRouter()


@router.get("/", response_model=List[DeviceInDB])
async def get_devices(
    current_user=Depends(get_current_user), skip: int = 0, limit: int = 100
):
    """获取设备列表"""
    try:
        devices = await DeviceService.get_devices(
            user_id=current_user.id, skip=skip, limit=limit
        )
        return devices
    except Exception as e:
        logger.error(f"获取设备列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取设备列表失败"
        )


@router.post("/", response_model=DeviceInDB)
async def create_device(
    device_data: DeviceCreate, current_user=Depends(get_current_user)
):
    """创建设备"""
    try:
        device = await DeviceService.create_device(
            user_id=current_user.id, device_data=device_data
        )
        return device
    except Exception as e:
        logger.error(f"创建设备失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="创建设备失败"
        )


@router.get("/{device_id}", response_model=DeviceInDB)
async def get_device(device_id: int, current_user=Depends(get_current_user)):
    """获取设备详情"""
    try:
        device = await DeviceService.get_device(
            user_id=current_user.id, device_id=device_id
        )
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在"
            )
        return device
    except Exception as e:
        logger.error(f"获取设备详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取设备详情失败"
        )


@router.put("/{device_id}", response_model=DeviceInDB)
async def update_device(
    device_id: int, device_data: DeviceUpdate, current_user=Depends(get_current_user)
):
    """更新设备"""
    try:
        device = await DeviceService.update_device(
            user_id=current_user.id, device_id=device_id, device_data=device_data
        )
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在"
            )
        return device
    except Exception as e:
        logger.error(f"更新设备失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="更新设备失败"
        )


@router.delete("/{device_id}")
async def delete_device(device_id: int, current_user=Depends(get_current_user)):
    """删除设备"""
    try:
        success = await DeviceService.delete_device(
            user_id=current_user.id, device_id=device_id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在"
            )
        return {"message": "设备删除成功"}
    except Exception as e:
        logger.error(f"删除设备失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除设备失败"
        )
