"""配置审计和通知服务"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.websocket import WebSocketManager
from ..models.audit import ConfigAudit
from ..models.models import SystemConfig, User

logger = logging.getLogger(__name__)


class AuditManager:
    """审计管理器"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.ws_manager = WebSocketManager()

    async def record_operation(
        self,
        config_key: str,
        operation: str,
        user_id: int,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        metadata: Optional[Dict] = None,
    ) -> ConfigAudit:
        """记录操作"""
        try:
            # 创建审计记录
            audit = ConfigAudit(
                config_key=config_key,
                operation=operation,
                old_value=json.dumps(old_value) if old_value is not None else None,
                new_value=json.dumps(new_value) if new_value is not None else None,
                metadata=metadata,
                user_id=user_id,
            )

            self.db.add(audit)
            await self.db.commit()
            await self.db.refresh(audit)

            # 发送通知
            await self._notify_change(audit)

            return audit

        except Exception as e:
            logger.error(f"记录审计失败: {str(e)}")
            await self.db.rollback()
            raise

    async def get_audit_logs(
        self,
        config_key: Optional[str] = None,
        operation: Optional[str] = None,
        user_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ConfigAudit]:
        """获取审计日志"""
        try:
            query = select(ConfigAudit).options(selectinload(ConfigAudit.user))

            # 添加过滤条件
            if config_key:
                query = query.where(ConfigAudit.config_key == config_key)

            if operation:
                query = query.where(ConfigAudit.operation == operation)

            if user_id:
                query = query.where(ConfigAudit.user_id == user_id)

            if start_time:
                query = query.where(ConfigAudit.created_at >= start_time)

            if end_time:
                query = query.where(ConfigAudit.created_at <= end_time)

            # 添加排序和分页
            query = (
                query.order_by(ConfigAudit.created_at.desc()).offset(skip).limit(limit)
            )

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"获取审计日志失败: {str(e)}")
            raise

    async def get_operation_stats(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, int]:
        """获取操作统计"""
        try:
            query = select(
                ConfigAudit.operation, func.count(ConfigAudit.id).label("count")
            ).group_by(ConfigAudit.operation)

            if start_time:
                query = query.where(ConfigAudit.created_at >= start_time)

            if end_time:
                query = query.where(ConfigAudit.created_at <= end_time)

            result = await self.db.execute(query)
            return {row[0]: row[1] for row in result}

        except Exception as e:
            logger.error(f"获取操作统计失败: {str(e)}")
            raise

    async def get_user_activities(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取用户活动"""
        try:
            query = (
                select(ConfigAudit)
                .where(ConfigAudit.user_id == user_id)
                .order_by(ConfigAudit.created_at.desc())
                .offset(skip)
                .limit(limit)
            )

            result = await self.db.execute(query)
            audits = result.scalars().all()

            return [
                {
                    "config_key": audit.config_key,
                    "operation": audit.operation,
                    "old_value": (
                        json.loads(audit.old_value) if audit.old_value else None
                    ),
                    "new_value": (
                        json.loads(audit.new_value) if audit.new_value else None
                    ),
                    "metadata": audit.metadata,
                    "created_at": audit.created_at,
                }
                for audit in audits
            ]

        except Exception as e:
            logger.error(f"获取用户活动失败: {str(e)}")
            raise

    async def _notify_change(self, audit: ConfigAudit):
        """发送变更通知"""
        try:
            # 构建通知消息
            message = {
                "type": "config_change",
                "data": {
                    "config_key": audit.config_key,
                    "operation": audit.operation,
                    "old_value": (
                        json.loads(audit.old_value) if audit.old_value else None
                    ),
                    "new_value": (
                        json.loads(audit.new_value) if audit.new_value else None
                    ),
                    "metadata": audit.metadata,
                    "user_id": audit.user_id,
                    "timestamp": audit.created_at.isoformat(),
                },
            }

            # 发送WebSocket通知
            await self.ws_manager.broadcast(json.dumps(message))

        except Exception as e:
            logger.error(f"发送通知失败: {str(e)}")


class AuditDecorator:
    """审计装饰器"""

    def __init__(self, audit_manager: AuditManager):
        self.audit_manager = audit_manager

    def audit_operation(
        self,
        operation: str,
        get_config_key=lambda *args, **kwargs: args[1] if len(args) > 1 else None,
    ):
        """审计操作装饰器"""

        def decorator(func):
            async def wrapper(*args, **kwargs):
                # 获取配置键
                config_key = get_config_key(*args, **kwargs)
                if not config_key:
                    return await func(*args, **kwargs)

                # 获取原值
                old_value = None
                try:
                    config = await args[0].db.get(SystemConfig, config_key)
                    if config:
                        old_value = config.value
                except Exception:
                    pass

                # 执行操作
                result = await func(*args, **kwargs)

                # 获取新值
                new_value = None
                try:
                    config = await args[0].db.get(SystemConfig, config_key)
                    if config:
                        new_value = config.value
                except Exception:
                    pass

                # 记录审计
                await self.audit_manager.record_operation(
                    config_key=config_key,
                    operation=operation,
                    user_id=kwargs.get("user_id"),
                    old_value=old_value,
                    new_value=new_value,
                    metadata=kwargs.get("metadata"),
                )

                return result

            return wrapper

        return decorator
