"""设备API"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ncod.master.services.device import device_service
from ncod.master.middleware.auth import get_current_user, require_permissions
from ncod.core.logger import setup_logger

logger = setup_logger("device_api")
router = APIRouter(prefix="/api/v1/devices")


class DeviceCreate(BaseModel):
    """创建设备请求"""

    name: str
    mac_address: str
    ip_address: Optional[str] = None
    description: Optional[str] = None
    organization_id: Optional[str] = None
    slave_id: Optional[str] = None


class DeviceUpdate(BaseModel):
    """更新设备请求"""

    name: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    organization_id: Optional[str] = None
    slave_id: Optional[str] = None


@router.post("")
@require_permissions(["device:create"])
async def create_device(request: DeviceCreate, user: dict = Depends(get_current_user)):
    """创建设备"""
    try:
        success, message, device = await device_service.create_device(request.dict())
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating device: {e}")
        raise HTTPException(status_code=500, detail="Failed to create device")


@router.put("/{device_id}")
@require_permissions(["device:update"])
async def update_device(
    device_id: str, request: DeviceUpdate, user: dict = Depends(get_current_user)
):
    """更新设备"""
    try:
        success, message, device = await device_service.update_device(
            device_id, request.dict(exclude_unset=True)
        )
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device: {e}")
        raise HTTPException(status_code=500, detail="Failed to update device")


@router.delete("/{device_id}")
@require_permissions(["device:delete"])
async def delete_device(device_id: str, user: dict = Depends(get_current_user)):
    """删除设备"""
    try:
        success, message = await device_service.delete_device(device_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"message": "Device deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete device")


@router.get("/{device_id}")
@require_permissions(["device:read"])
async def get_device(device_id: str, user: dict = Depends(get_current_user)):
    """获取设备"""
    try:
        device = await device_service.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        return device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device")


@router.get("")
@require_permissions(["device:read"])
async def list_devices(
    organization_id: Optional[str] = None,
    slave_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """获取设备列表"""
    try:
        return await device_service.list_devices(organization_id, slave_id)
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to list devices")
