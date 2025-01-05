"""设备API路由"""

from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from ncod.core.logger import setup_logger
from ncod.slave.core.deps import get_device_manager, get_device_controller
from ncod.slave.device.manager import DeviceManager
from ncod.slave.device.controller import DeviceController

router = APIRouter()
logger = setup_logger("device_routes")


@router.get("/devices")
async def get_devices(
    device_manager: DeviceManager = Depends(get_device_manager),
) -> List[Dict]:
    """获取所有设备"""
    try:
        devices = device_manager.get_all_devices()
        return list(devices.values())
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get devices",
        )


@router.get("/devices/{device_id}")
async def get_device(
    device_id: str, device_controller: DeviceController = Depends(get_device_controller)
) -> Dict:
    """获取设备信息"""
    try:
        device_info = await device_controller.get_device_info(device_id)
        if not device_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
            )
        return device_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device info",
        )


@router.post("/devices/{device_id}/connect")
async def connect_device(
    device_id: str, device_controller: DeviceController = Depends(get_device_controller)
) -> Dict:
    """连接设备"""
    try:
        success = await device_controller.connect_device(device_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to connect device",
            )
        return {"status": "connected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect device",
        )


@router.post("/devices/{device_id}/disconnect")
async def disconnect_device(
    device_id: str, device_controller: DeviceController = Depends(get_device_controller)
) -> Dict:
    """断开设备连接"""
    try:
        success = await device_controller.disconnect_device(device_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to disconnect device",
            )
        return {"status": "disconnected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect device",
        )
