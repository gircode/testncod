"""
数据同步端点
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.session import get_db
from ....schemas.sync import SyncRequest, SyncResponse
from ....services.sync import SyncService

router = APIRouter()


@router.post("/start")
async def start_sync(db: AsyncSession = Depends(get_db)) -> dict:
    """启动同步"""
    sync_service = SyncService(db)
    await sync_service.start()
    return {"status": "started"}


@router.post("/stop")
async def stop_sync(db: AsyncSession = Depends(get_db)) -> dict:
    """停止同步"""
    sync_service = SyncService(db)
    await sync_service.stop()
    return {"status": "stopped"}


@router.post("/data", response_model=SyncResponse)
async def sync_data(
    request: SyncRequest, db: AsyncSession = Depends(get_db)
) -> SyncResponse:
    """同步数据"""
    sync_service = SyncService(db)
    return await sync_service.sync_data(request)


@router.get("/status")
async def get_sync_status(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """获取同步状态"""
    sync_service = SyncService(db)
    return await sync_service.get_status()


@router.get("/history")
async def get_sync_history(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取同步历史"""
    sync_service = SyncService(db)
    return await sync_service.get_history(skip, limit)


@router.post("/reset")
async def reset_sync(db: AsyncSession = Depends(get_db)) -> dict:
    """重置同步"""
    sync_service = SyncService(db)
    await sync_service.reset()
    return {"status": "reset"}
