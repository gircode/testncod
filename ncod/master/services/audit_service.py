from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.organization import AuditLog
from ..core.logger import logger


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """记录审计日志"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=str(details) if details else None,
                ip_address=ip_address,
            )

            self.db.add(audit_log)
            await self.db.commit()

        except Exception as e:
            logger.error(f"记录审计日志失败: {str(e)}")
            await self.db.rollback()
            raise

    async def get_user_actions(
        self,
        user_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        action_type: Optional[str] = None,
    ) -> list:
        """获取用户操作记录"""
        query = select(AuditLog).where(AuditLog.user_id == user_id)

        if start_time:
            query = query.where(AuditLog.created_at >= start_time)
        if end_time:
            query = query.where(AuditLog.created_at <= end_time)
        if action_type:
            query = query.where(AuditLog.action == action_type)

        result = await self.db.execute(query.order_by(AuditLog.created_at.desc()))
        return result.scalars().all()

    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list:
        """获取资源操作历史"""
        query = select(AuditLog).where(
            AuditLog.resource_type == resource_type, AuditLog.resource_id == resource_id
        )

        if start_time:
            query = query.where(AuditLog.created_at >= start_time)
        if end_time:
            query = query.where(AuditLog.created_at <= end_time)

        result = await self.db.execute(query.order_by(AuditLog.created_at.desc()))
        return result.scalars().all()
