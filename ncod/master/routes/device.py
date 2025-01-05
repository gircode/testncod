"""设备管理路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from ncod.master.models.device import Device, DeviceCreate, DeviceUpdate
from ncod.master.services.device_monitor import device_monitor
from ncod.master.services.websocket_service import websocket_manager
from ncod.utils.dependencies import get_current_user, get_current_admin_user
from ncod.utils.db import get_db

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("/", response_model=List[Device])
async def list_devices(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    """获取设备列表"""
    devices = await Device.get_all(db)
    return devices


@router.get("/{device_id}", response_model=Device)
async def get_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取设备详情"""
    device = await Device.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.post("/", response_model=Device)
async def create_device(
    device: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin_user),
):
    """创建设备"""
    new_device = await Device.create(db, device)
    return new_device


@router.put("/{device_id}", response_model=Device)
async def update_device(
    device_id: str,
    device: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin_user),
):
    """更新设备"""
    updated_device = await Device.update(db, device_id, device)
    if not updated_device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return updated_device


@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin_user),
):
    """删除设备"""
    success = await Device.delete(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="设备不存在")
    return {"message": "设备已删除"}


@router.post("/{device_id}/connect")
async def connect_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """连接设备"""
    device = await Device.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    success = await device_monitor.connect_device(device_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=400, detail="连接设备失败")

    return {"message": "设备已连接"}


@router.post("/{device_id}/disconnect")
async def disconnect_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """断开设备连接"""
    device = await Device.get_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    success = await device_monitor.disconnect_device(device_id)
    if not success:
        raise HTTPException(status_code=400, detail="断开设备连接失败")

    return {"message": "设备已断开连接"}


@router.websocket("/ws/{device_id}")
async def device_websocket(websocket: WebSocket, device_id: str):
    """设备WebSocket连接"""
    await websocket_manager.connect(websocket, "device")
    try:
        while True:
            data = await websocket.receive_json()
            # 处理接收到的消息
            await websocket_manager.broadcast(
                {"device_id": device_id, "data": data}, "device"
            )
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, "device")
