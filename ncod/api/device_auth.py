"""设备授权管理API"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ncod.core.db import get_db
from ncod.core.auth import get_current_user
from ncod.models.device import AuthorizedDevice, DeviceAuthLog
from ncod.schemas.device import (
    AuthorizedDeviceCreate,
    AuthorizedDeviceUpdate,
    AuthorizedDeviceResponse,
    DeviceAuthLogResponse,
)

router = APIRouter(prefix="/api/v1/device-auth", tags=["设备授权"])


@router.post("/devices", response_model=AuthorizedDeviceResponse)
async def create_authorized_device(
    device: AuthorizedDeviceCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建授权设备"""
    if not current_user.has_permission("device_auth.create"):
        raise HTTPException(status_code=403, detail="没有创建设备授权的权限")

    # 检查设备是否已存在
    existing_device = (
        db.query(AuthorizedDevice)
        .filter(
            AuthorizedDevice.vendor_id == device.vendor_id,
            AuthorizedDevice.product_id == device.product_id,
            AuthorizedDevice.serial_number == device.serial_number,
        )
        .first()
    )

    if existing_device:
        raise HTTPException(status_code=400, detail="设备已在授权列表中")

    # 创建新的授权设备
    db_device = AuthorizedDevice(
        **device.dict(),
        authorized_by=current_user.username,
        authorized_at=datetime.now()
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)

    return db_device


@router.get("/devices", response_model=List[AuthorizedDeviceResponse])
async def list_authorized_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    vendor_id: Optional[str] = None,
    product_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取授权设备列表"""
    if not current_user.has_permission("device_auth.view"):
        raise HTTPException(status_code=403, detail="没有查看设备授权的权限")

    query = db.query(AuthorizedDevice)

    if vendor_id:
        query = query.filter(AuthorizedDevice.vendor_id == vendor_id)
    if product_id:
        query = query.filter(AuthorizedDevice.product_id == product_id)
    if is_active is not None:
        query = query.filter(AuthorizedDevice.is_active == is_active)

    total = query.count()
    devices = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": devices,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit,
    }


@router.put("/devices/{device_id}", response_model=AuthorizedDeviceResponse)
async def update_authorized_device(
    device_id: int,
    device_update: AuthorizedDeviceUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新授权设备"""
    if not current_user.has_permission("device_auth.update"):
        raise HTTPException(status_code=403, detail="没有更新设备授权的权限")

    db_device = (
        db.query(AuthorizedDevice).filter(AuthorizedDevice.id == device_id).first()
    )

    if not db_device:
        raise HTTPException(status_code=404, detail="设备未找到")

    # 更新设备信息
    for field, value in device_update.dict(exclude_unset=True).items():
        setattr(db_device, field, value)

    db.commit()
    db.refresh(db_device)

    return db_device


@router.delete("/devices/{device_id}")
async def delete_authorized_device(
    device_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除授权设备"""
    if not current_user.has_permission("device_auth.delete"):
        raise HTTPException(status_code=403, detail="没有删除设备授权的权限")

    db_device = (
        db.query(AuthorizedDevice).filter(AuthorizedDevice.id == device_id).first()
    )

    if not db_device:
        raise HTTPException(status_code=404, detail="设备未找到")

    db.delete(db_device)
    db.commit()

    return {"message": "设备授权已删除"}


@router.get("/logs", response_model=List[DeviceAuthLogResponse])
async def list_auth_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    device_id: Optional[str] = None,
    is_authorized: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取授权日志列表"""
    if not current_user.has_permission("device_auth.view_logs"):
        raise HTTPException(status_code=403, detail="没有查看授权日志的权限")

    query = db.query(DeviceAuthLog)

    if device_id:
        query = query.filter(DeviceAuthLog.device_id == device_id)
    if is_authorized is not None:
        query = query.filter(DeviceAuthLog.is_authorized == is_authorized)
    if start_time:
        query = query.filter(DeviceAuthLog.check_time >= start_time)
    if end_time:
        query = query.filter(DeviceAuthLog.check_time <= end_time)

    total = query.count()
    logs = (
        query.order_by(DeviceAuthLog.check_time.desc()).offset(skip).limit(limit).all()
    )

    return {
        "total": total,
        "items": logs,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit,
    }
