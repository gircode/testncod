"""通知配置API路由"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ncod.master.services.notify_config import notify_config_service
from ncod.master.middleware.auth import get_current_user, require_permissions
from ncod.core.logger import setup_logger

logger = setup_logger("notify_config_api")
router = APIRouter(prefix="/api/v1/notify-configs")


class ConfigCreate(BaseModel):
    """创建配置请求"""

    name: str
    channel: str
    config: dict
    description: Optional[str] = None


class ConfigUpdate(BaseModel):
    """更新配置请求"""

    name: Optional[str] = None
    config: Optional[dict] = None
    description: Optional[str] = None


@router.post("")
@require_permissions(["notify:write"])
async def create_notify_config(
    config: ConfigCreate, user: dict = Depends(get_current_user)
):
    """创建通知配置"""
    try:
        result = await notify_config_service.create_config(
            config.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(
                status_code=500, detail="Failed to create notify config"
            )
        return result
    except Exception as e:
        logger.error(f"Error creating notify config: {e}")
        raise HTTPException(status_code=500, detail="Failed to create notify config")


@router.get("")
@require_permissions(["notify:read"])
async def get_notify_configs(
    channel: Optional[str] = None, user: dict = Depends(get_current_user)
):
    """获取通知配置"""
    try:
        return await notify_config_service.get_channel_configs(channel)
    except Exception as e:
        logger.error(f"Error getting notify configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notify configs")


@router.put("/{config_id}")
@require_permissions(["notify:write"])
async def update_notify_config(
    config_id: str, config: ConfigUpdate, user: dict = Depends(get_current_user)
):
    """更新通知配置"""
    try:
        result = await notify_config_service.update_config(
            config_id, config.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=404, detail="Notify config not found")
        return result
    except Exception as e:
        logger.error(f"Error updating notify config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notify config")


@router.delete("/{config_id}")
@require_permissions(["notify:write"])
async def delete_notify_config(config_id: str, user: dict = Depends(get_current_user)):
    """删除通知配置"""
    try:
        success = await notify_config_service.delete_config(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notify config not found")
        return {"message": "Notify config deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting notify config: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notify config")
