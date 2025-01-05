"""
WebSocket接口
"""

import logging
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from ncod.master.app.core.deps import get_current_active_user
from ncod.master.app.core.security import check_admin_permission
from ncod.master.app.db.session import get_db
from ncod.master.app.models.auth import User
from ncod.master.app.models.config import Config
from ncod.master.app.services.notification import notification_manager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/config")
async def config_websocket(
    websocket: WebSocket,
    keys: Optional[List[str]] = Query(None),
    groups: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    配置变更WebSocket接口

    用于接收配置变更通知

    参数:
    - keys: 要订阅的配置键列表
    - groups: 要订阅的配置组列表

    权限:
    - 普通用户只能订阅公开配置
    - 管理员可以订阅所有配置
    """
    try:
        # 检查权限
        is_admin = await check_admin_permission(current_user)
        if not is_admin:
            # 非管理员只能订阅公开配置
            # 获取可访问的配置键
            query = select(Config.key).where(Config.is_public == True)
            if keys:
                query = query.where(Config.key.in_(keys))
            result = await db.execute(query)
            allowed_keys = [r[0] for r in result]

            # 获取可访问的配置组
            query = select(Config.group).where(Config.is_public == True).distinct()
            if groups:
                query = query.where(Config.group.in_(groups))
            result = await db.execute(query)
            allowed_groups = [r[0] for r in result if r[0]]

            # 过滤订阅列表
            keys = [k for k in (keys or []) if k in allowed_keys]
            groups = [g for g in (groups or []) if g in allowed_groups]

        # 订阅配置变更
        await notification_manager.subscribe(
            websocket=websocket, keys=keys, groups=groups
        )

        try:
            while True:
                # 保持连接活跃
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")

        except WebSocketDisconnect:
            # 连接断开时取消订阅
            await notification_manager.unsubscribe(websocket)

    except Exception as e:
        logger.error(f"WebSocket连接失败: {str(e)}")
        await websocket.close()


@router.get("/ws/stats")
async def get_websocket_stats(current_user: User = Depends(get_current_active_user)):
    """
    获取WebSocket连接统计

    返回当前的订阅者数量统计

    权限:
    - 仅管理员可访问
    """
    # 检查权限
    if not await check_admin_permission(current_user):
        raise HTTPException(status_code=403, detail="无权访问此接口")

    return notification_manager.get_subscriber_count()
