"""设备路由"""

from fastapi import APIRouter, HTTPException
from ncod.core.config import config

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("/status")
async def get_device_status():
    """获取设备状态"""
    return {"status": "ok"}
