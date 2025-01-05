"""告警规则API路由"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ncod.master.services.alert_rule import alert_rule_service
from ncod.master.middleware.auth import get_current_user, require_permissions
from ncod.core.logger import setup_logger

logger = setup_logger("alert_rule_api")
router = APIRouter(prefix="/api/v1/alert-rules")


class RuleCreate(BaseModel):
    """创建规则请求"""

    name: str
    metric_type: str
    condition: str
    threshold: float
    level: str
    enabled: Optional[bool] = True
    notify_channels: Optional[dict] = {}
    description: Optional[str] = None


class RuleUpdate(BaseModel):
    """更新规则请求"""

    name: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    level: Optional[str] = None
    enabled: Optional[bool] = None
    notify_channels: Optional[dict] = None
    description: Optional[str] = None


@router.post("/device/{device_id}")
@require_permissions(["alert:write"])
async def create_alert_rule(
    device_id: str, rule: RuleCreate, user: dict = Depends(get_current_user)
):
    """创建告警规则"""
    try:
        result = await alert_rule_service.create_rule(
            device_id, rule.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create alert rule")
        return result
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert rule")


@router.get("/device/{device_id}")
@require_permissions(["alert:read"])
async def get_device_rules(
    device_id: str,
    enabled: Optional[bool] = None,
    user: dict = Depends(get_current_user),
):
    """获取设备告警规则"""
    try:
        return await alert_rule_service.get_device_rules(device_id, enabled)
    except Exception as e:
        logger.error(f"Error getting device rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device rules")


@router.put("/{rule_id}")
@require_permissions(["alert:write"])
async def update_alert_rule(
    rule_id: str, rule: RuleUpdate, user: dict = Depends(get_current_user)
):
    """更新告警规则"""
    try:
        result = await alert_rule_service.update_rule(
            rule_id, rule.dict(exclude_unset=True)
        )
        if not result:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        return result
    except Exception as e:
        logger.error(f"Error updating alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert rule")


@router.delete("/{rule_id}")
@require_permissions(["alert:write"])
async def delete_alert_rule(rule_id: str, user: dict = Depends(get_current_user)):
    """删除告警规则"""
    try:
        success = await alert_rule_service.delete_rule(rule_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        return {"message": "Alert rule deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert rule")
