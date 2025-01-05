"""监控配置API路由"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ncod.master.services.monitor_config import monitor_config_service
from ncod.master.middleware.auth import get_current_user, require_permissions
from ncod.core.logger import setup_logger

logger = setup_logger("monitor_config_api")
router = APIRouter(prefix="/api/v1/monitor-configs")


class ConfigCreate(BaseModel):
    """创建配置请求"""

    metric_type: str
    enabled: Optional[bool] = True
    threshold: Optional[float] = None
    interval: Optional[int] = 30
    alert_levels: Optional[dict] = {}
    description: Optional[str] = None


class ConfigUpdate(BaseModel):
    """更新配置请求"""

    enabled: Optional[bool] = None
    threshold: Optional[float] = None
    interval: Optional[int] = None
    alert_levels: Optional[dict] = None
    description: Optional[str] = None


@router.post("/device/{device_id}")
@require_permissions(["monitor:write"])
async def create_monitor_config(
    device_id: str, config: ConfigCreate, user: dict = Depends(get_current_user)
):
    """创建监控配置"""
    try:
        result = await monitor_config_service.create_config(
            device_id, config.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(
                status_code=500, detail="Failed to create monitor config"
            )
        return result
    except Exception as e:
        logger.error(f"Error creating monitor config: {e}")
        raise HTTPException(status_code=500, detail="Failed to create monitor config")


@router.get("/device/{device_id}")
@require_permissions(["monitor:read"])
async def get_device_configs(device_id: str, user: dict = Depends(get_current_user)):
    """获取设备监控配置"""
    try:
        return await monitor_config_service.get_device_configs(device_id)
    except Exception as e:
        logger.error(f"Error getting device configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device configs")


@router.put("/{config_id}")
@require_permissions(["monitor:write"])
async def update_monitor_config(
    config_id: str, config: ConfigUpdate, user: dict = Depends(get_current_user)
):
    """更新监控配置"""
    try:
        result = await monitor_config_service.update_config(
            config_id, config.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=404, detail="Monitor config not found")
        return result
    except Exception as e:
        logger.error(f"Error updating monitor config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update monitor config")
