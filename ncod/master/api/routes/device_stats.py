"""设备统计API"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from ncod.master.auth import get_current_user
from ncod.master.services.device_stats import DeviceStatsService

router = APIRouter()


@router.get("/devices/{device_id}/stats")
async def get_device_stats(device_id: str, _=Depends(get_current_user)):
    try:
        stats = await DeviceStatsService.get_device_stats(device_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Device stats not found")
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get device stats") from e


@router.get("/devices/{device_id}/history")
async def get_device_history(
    device_id: str,
    start_time: datetime,
    end_time: datetime,
    _=Depends(get_current_user),
):
    try:
        history = await DeviceStatsService.get_device_history(
            device_id, start_time, end_time
        )
        return history
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Failed to get device history"
        ) from e
