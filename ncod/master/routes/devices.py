from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    WebSocket,
    BackgroundTasks,
)
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import pandas as pd
import os
import asyncio
import uuid

from ncod.core.db.database import get_db
from ncod.master.models.device import Device, DeviceStatus
from ncod.master.models.device_history import DeviceHistory
from ncod.master.schemas.device import DeviceCreate, DeviceResponse, DeviceAssign
from ncod.master.auth import get_current_user
from ncod.master.websocket import ConnectionManager
from ncod.master.auth.permissions import require_permissions
from ncod.master.models.permission import Permission
from ncod.master.services.device_stats import DeviceStatsService
from ncod.master.services.export_manager import ExportManager
from ncod.master.services.cache_manager import CacheManager
from ncod.master.exceptions import (
    DeviceNotFoundError,
    DeviceBusyError,
    DeviceOfflineError,
    PermissionDeniedError,
)

router = APIRouter(prefix="/api/v1/devices", tags=["设备管理"])
ws_manager = ConnectionManager()
export_manager = ExportManager()
cache_manager = CacheManager()


@router.get("/", response_model=List[DeviceResponse])
@require_permissions(Permission.DEVICE_VIEW)
async def get_devices(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """获取设备列表"""
    devices = db.query(Device).all()
    return devices


@router.post("/{device_id}/assign", response_model=dict)
async def assign_device(
    device_id: int,
    assign_data: DeviceAssign,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """分配设备给用户"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device.status == DeviceStatus.IN_USE:
        raise HTTPException(status_code=400, detail="Device is already in use")

    # 创建使用记录
    history = DeviceHistory(
        device_id=device_id,
        user_id=assign_data.user_id,
        start_time=datetime.utcnow(),
        status="active",
    )

    device.status = DeviceStatus.IN_USE
    device.current_user_id = assign_data.user_id

    db.add(history)
    db.commit()

    return {"message": "Device assigned successfully"}


@router.post("/{device_id}/release")
async def release_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """释放设备"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 更新使用记录
    history = (
        db.query(DeviceHistory)
        .filter(DeviceHistory.device_id == device_id)
        .filter(DeviceHistory.status == "active")
        .first()
    )

    if history:
        history.end_time = datetime.utcnow()
        history.status = "completed"

    device.status = DeviceStatus.ONLINE
    device.current_user_id = None

    db.commit()

    return {"message": "Device released successfully"}


@router.post("/{device_id}/connect")
@require_permissions(Permission.DEVICE_CONNECT)
async def connect_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """连接设备"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise DeviceNotFoundError(device_id)

    # 检查权限
    if (
        not current_user.is_admin
        and device.organization_id != current_user.organization_id
    ):
        raise PermissionDeniedError()

    # 检查设备状态
    if device.status == DeviceStatus.OFFLINE:
        raise DeviceOfflineError(device_id)

    if device.status == DeviceStatus.IN_USE:
        raise DeviceBusyError(device_id)

    try:
        # 更新设备状态
        device.status = DeviceStatus.IN_USE
        device.current_user_id = current_user.id
        db.commit()

        # 尝试建立连接
        await ws_manager.connect(device_id)

        return {"message": "Device connected successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to connect device {device_id}", exc_info=e)
        raise DeviceError(
            code="CONNECTION_FAILED",
            message="Failed to establish connection",
            status_code=500,
        )


@router.post("/{device_id}/disconnect", response_model=dict)
async def disconnect_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """断开设备连接"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise DeviceNotFoundError(device_id)

    if device.current_user_id != current_user.id:
        raise PermissionDeniedError()

    try:
        await ws_manager.disconnect(device_id)

        device.status = DeviceStatus.IDLE
        device.current_user_id = None
        db.commit()

        return {"message": "Device disconnected successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to disconnect device {device_id}", exc_info=e)
        raise DeviceError(
            code="DISCONNECT_FAILED",
            message="Failed to disconnect device",
            status_code=500,
        )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接端点"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # 处理从服务器的状态更新
            if data["type"] == "status_update":
                await handle_status_update(data)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)


async def handle_status_update(data: dict):
    """处理设备状态更新"""
    try:
        device_id = data["device_id"]
        status = data["status"]

        async with get_db() as db:
            device = db.query(Device).filter(Device.id == device_id).first()
            if device:
                device.status = status
                device.last_seen = datetime.utcnow()
                db.commit()

                # 广播状态更新给所有客户端
                await ws_manager.broadcast(
                    {"type": "device_status", "device_id": device_id, "status": status}
                )
    except Exception as e:
        print(f"Error handling status update: {e}")


@router.post("/{device_id}/manage")
@require_permissions(Permission.DEVICE_MANAGE)
async def manage_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """管理设备配置"""
    # ... 设备管理逻辑 ...


@router.get("/{device_id}/stats", response_model=dict)
@require_permissions(Permission.DEVICE_VIEW)
async def get_device_stats(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取设备统计"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    stats_service = DeviceStatsService(db, cache_manager)
    stats = await stats_service.get_device_stats(device_id)
    return stats


@router.get("/organization/{org_id}/stats", response_model=dict)
@require_permissions([Permission.DEVICE_VIEW, Permission.ORG_VIEW], require_all=True)
async def get_organization_stats(
    org_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """获取组织统计"""
    if current_user.organization_id != org_id and not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Not authorized to view this organization's stats"
        )

    cache_key = f"org_stats_{org_id}"

    async def fetch_stats():
        stats_service = DeviceStatsService(db, cache_manager)
        return await stats_service.get_organization_stats(org_id)

    return await cache_manager.get_or_set("stats", cache_key, fetch_stats, ttl=600)


@router.post("/{device_id}/stats/export")
@require_permissions(Permission.DEVICE_VIEW)
async def create_export_task(
    device_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建设备统计导出任务"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    task_id = str(uuid.uuid4())
    task = await export_manager.create_export_task(task_id)

    background_tasks.add_task(export_manager.export_device_stats, db, device_id, task)

    return {"task_id": task_id, "status": task.status}


@router.get("/export/{task_id}/status")
async def get_export_status(task_id: str):
    """获取导出任务状态"""
    task = export_manager.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"status": task.status, "progress": task.progress, "error": task.error}


@router.get("/export/{task_id}/download")
async def download_export(task_id: str):
    """下载导出文件"""
    task = export_manager.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Export not ready")

    if not os.path.exists(task.file_path):
        raise HTTPException(status_code=404, detail="Export file not found")

    return FileResponse(
        task.file_path,
        filename=os.path.basename(task.file_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/organization/{org_id}/stats/export")
@require_permissions([Permission.DEVICE_VIEW, Permission.ORG_VIEW], require_all=True)
async def export_organization_stats(
    org_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """导出组织的设备使用统计"""
    if current_user.organization_id != org_id and not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Not authorized to view this organization's stats"
        )

    filename = f"org_stats_{org_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = f"temp/exports/{filename}"

    os.makedirs("temp/exports", exist_ok=True)

    stats_service = DeviceStatsService(db)
    stats_data = await stats_service.get_organization_stats_for_export(org_id)

    writer = pd.ExcelWriter(filepath, engine="xlsxwriter")

    # 组织设备统计
    pd.DataFrame(stats_data["device_stats"]).to_excel(
        writer, sheet_name="设备统计", index=False
    )

    # 用户使用统计
    pd.DataFrame(stats_data["user_stats"]).to_excel(
        writer, sheet_name="用户统计", index=False
    )

    writer.close()

    background_tasks.add_task(cleanup_export_file, filepath)

    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


async def cleanup_export_file(filepath: str):
    """清理导出文件"""
    await asyncio.sleep(6 * 3600)  # 6小时后删除
    try:
        os.remove(filepath)
    except Exception as e:
        logger.error(f"Error cleaning up export file {filepath}: {e}")
