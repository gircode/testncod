"""
配置变更通知服务
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import WebSocket
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ConfigChangeEvent(BaseModel):
    """配置变更事件"""

    key: str
    old_value: Optional[str]
    new_value: str
    changed_by: int
    changed_at: datetime
    group: Optional[str]


class NotificationManager:
    """通知管理器"""

    def __init__(self):
        self._subscribers: Dict[str, Set[WebSocket]] = {}
        self._group_subscribers: Dict[str, Set[WebSocket]] = {}

    async def subscribe(
        self,
        websocket: WebSocket,
        keys: Optional[List[str]] = None,
        groups: Optional[List[str]] = None,
    ):
        """订阅配置变更"""
        try:
            await websocket.accept()

            # 订阅特定配置
            if keys:
                for key in keys:
                    if key not in self._subscribers:
                        self._subscribers[key] = set()
                    self._subscribers[key].add(websocket)

            # 订阅配置组
            if groups:
                for group in groups:
                    if group not in self._group_subscribers:
                        self._group_subscribers[group] = set()
                    self._group_subscribers[group].add(websocket)

            # 发送确认消息
            await websocket.send_json(
                {
                    "type": "subscribe",
                    "status": "success",
                    "keys": keys,
                    "groups": groups,
                }
            )

        except Exception as e:
            logger.error(f"订阅配置变更失败: {str(e)}")
            await websocket.close()

    async def unsubscribe(self, websocket: WebSocket):
        """取消订阅"""
        try:
            # 从所有订阅中移除
            for subscribers in self._subscribers.values():
                subscribers.discard(websocket)

            for subscribers in self._group_subscribers.values():
                subscribers.discard(websocket)

            await websocket.close()

        except Exception as e:
            logger.error(f"取消订阅失败: {str(e)}")

    async def notify_change(self, event: ConfigChangeEvent):
        """通知配置变更"""
        try:
            # 获取需要通知的订阅者
            subscribers = set()

            # 添加配置键的订阅者
            if event.key in self._subscribers:
                subscribers.update(self._subscribers[event.key])

            # 添加配置组的订阅者
            if event.group and event.group in self._group_subscribers:
                subscribers.update(self._group_subscribers[event.group])

            # 发送通知
            message = {"type": "config_change", "data": event.dict()}

            for websocket in subscribers:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"发送通知失败: {str(e)}")
                    await self.unsubscribe(websocket)

        except Exception as e:
            logger.error(f"通知配置变更失败: {str(e)}")

    async def broadcast(self, message: Dict):
        """广播消息给所有订阅者"""
        try:
            # 获取所有订阅者
            subscribers = set()
            for subs in self._subscribers.values():
                subscribers.update(subs)
            for subs in self._group_subscribers.values():
                subscribers.update(subs)

            # 发送消息
            for websocket in subscribers:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"广播消息失败: {str(e)}")
                    await self.unsubscribe(websocket)

        except Exception as e:
            logger.error(f"广播消息失败: {str(e)}")

    def get_subscriber_count(self) -> Dict[str, int]:
        """获取订阅者数量统计"""
        stats = {"total": 0, "by_key": {}, "by_group": {}}

        # 统计按键订阅
        for key, subscribers in self._subscribers.items():
            count = len(subscribers)
            stats["by_key"][key] = count
            stats["total"] += count

        # 统计按组订阅
        for group, subscribers in self._group_subscribers.items():
            count = len(subscribers)
            stats["by_group"][group] = count
            stats["total"] += count

        return stats


# 创建全局通知管理器实例
notification_manager = NotificationManager()
