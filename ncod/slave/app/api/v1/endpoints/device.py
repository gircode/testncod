"""
设备管理端点
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.session import get_db
from ....models.device import Device
from ....schemas.device import DeviceCreate, DeviceInDB, DeviceUpdate

router = APIRouter()


@router.post("/register", response_model=DeviceInDB)
async def register_device(
    device: DeviceCreate, db: AsyncSession = Depends(get_db)
) -> DeviceInDB:
    """注册设备"""
    db_device = Device(**device.dict())
    db.add(db_device)
    await db.commit()
    await db.refresh(db_device)
    return db_device


@router.post("/{device_id}/connect")
async def connect_device(device_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """连接设备"""
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    device.is_connected = True
    await db.commit()
    return {"status": "connected"}


@router.post("/{device_id}/disconnect")
async def disconnect_device(device_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """断开设备"""
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    device.is_connected = False
    await db.commit()
    return {"status": "disconnected"}


@router.get("/", response_model=List[DeviceInDB])
async def get_devices(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
) -> List[DeviceInDB]:
    """获取设备列表"""
    result = await db.execute(select(Device).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{device_id}", response_model=DeviceInDB)
async def get_device(device_id: str, db: AsyncSession = Depends(get_db)) -> DeviceInDB:
    """获取设备详情"""
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.put("/{device_id}", response_model=DeviceInDB)
async def update_device(
    device_id: str, device: DeviceUpdate, db: AsyncSession = Depends(get_db)
) -> DeviceInDB:
    """更新设备"""
    db_device = await db.get(Device, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="设备不存在")

    for field, value in device.dict(exclude_unset=True).items():
        setattr(db_device, field, value)

    await db.commit()
    await db.refresh(db_device)
    return db_device


@router.delete("/{device_id}")
async def delete_device(device_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """删除设备"""
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    await db.delete(device)
    await db.commit()
    return {"status": "deleted"}
