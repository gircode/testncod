"""
审计日志服务
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.audit_log import AuditLog
from ..models.user import User


class AuditService:
    """审计日志服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        action: str,
        status: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """记录审计事件"""
        log = AuditLog(
            user_id=user_id,
            action=action,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            error_message=error_message,
        )

        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_logs(
        self,
        page: int = 1,
        per_page: int = 20,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> tuple[List[AuditLog], int]:
        """获取审计日志"""
        query = select(AuditLog)

        # 应用过滤条件
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if status:
            query = query.filter(AuditLog.status == status)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        if search:
            query = query.filter(
                or_(
                    AuditLog.action.ilike(f"%{search}%"),
                    AuditLog.resource_type.ilike(f"%{search}%"),
                    AuditLog.resource_id.ilike(f"%{search}%"),
                    AuditLog.error_message.ilike(f"%{search}%"),
                )
            )

        # 计算总数
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))

        # 应用分页和排序
        query = query.order_by(desc(AuditLog.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        return logs, total

    async def get_user_activity(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取用户活动统计"""
        start_date = datetime.utcnow() - timedelta(days=days)

        # 获取用户的所有日志
        query = select(AuditLog).where(
            and_(AuditLog.user_id == user_id, AuditLog.created_at >= start_date)
        )
        result = await self.db.execute(query)
        logs = result.scalars().all()

        # 统计活动
        activity_stats = {
            "total_actions": len(logs),
            "success_rate": (
                sum(1 for log in logs if log.status == "success") / len(logs)
                if logs
                else 0
            ),
            "action_distribution": {},
            "resource_distribution": {},
            "daily_activity": {},
            "error_count": sum(1 for log in logs if log.status == "error"),
        }

        # 统计动作分布
        for log in logs:
            activity_stats["action_distribution"][log.action] = (
                activity_stats["action_distribution"].get(log.action, 0) + 1
            )

            if log.resource_type:
                activity_stats["resource_distribution"][log.resource_type] = (
                    activity_stats["resource_distribution"].get(log.resource_type, 0)
                    + 1
                )

            date = log.created_at.date().isoformat()
            activity_stats["daily_activity"][date] = (
                activity_stats["daily_activity"].get(date, 0) + 1
            )

        return activity_stats

    async def get_security_metrics(self, days: int = 30) -> Dict[str, Any]:
        """获取安全指标"""
        start_date = datetime.utcnow() - timedelta(days=days)

        # 获取所有安全相关的日志
        query = select(AuditLog).where(
            and_(
                AuditLog.created_at >= start_date,
                AuditLog.action.in_(
                    [
                        "login",
                        "logout",
                        "password_change",
                        "2fa_setup",
                        "2fa_verify",
                        "permission_change",
                    ]
                ),
            )
        )
        result = await self.db.execute(query)
        logs = result.scalars().all()

        metrics = {
            "login_success_rate": 0,
            "failed_login_attempts": 0,
            "password_changes": 0,
            "2fa_adoption_rate": 0,
            "suspicious_activities": 0,
            "daily_metrics": {},
        }

        # 统计登录成功率
        login_logs = [log for log in logs if log.action == "login"]
        if login_logs:
            successful_logins = sum(1 for log in login_logs if log.status == "success")
            metrics["login_success_rate"] = successful_logins / len(login_logs)
            metrics["failed_login_attempts"] = len(login_logs) - successful_logins

        # 统计密码修改
        metrics["password_changes"] = sum(
            1 for log in logs if log.action == "password_change"
        )

        # 统计2FA使用率
        total_users = await self.db.scalar(select(func.count()).select_from(User))
        users_with_2fa = await self.db.scalar(
            select(func.count()).select_from(User).where(User.is_2fa_enabled == True)
        )
        metrics["2fa_adoption_rate"] = (
            users_with_2fa / total_users if total_users > 0 else 0
        )

        # 统计可疑活动
        metrics["suspicious_activities"] = sum(
            1 for log in logs if log.details and log.details.get("suspicious", False)
        )

        # 按日统计
        for log in logs:
            date = log.created_at.date().isoformat()
            if date not in metrics["daily_metrics"]:
                metrics["daily_metrics"][date] = {
                    "total_events": 0,
                    "successful_events": 0,
                    "failed_events": 0,
                    "suspicious_events": 0,
                }

            metrics["daily_metrics"][date]["total_events"] += 1
            if log.status == "success":
                metrics["daily_metrics"][date]["successful_events"] += 1
            elif log.status in ["failure", "error"]:
                metrics["daily_metrics"][date]["failed_events"] += 1

            if log.details and log.details.get("suspicious", False):
                metrics["daily_metrics"][date]["suspicious_events"] += 1

        return metrics

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """清理旧日志"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = delete(AuditLog).where(AuditLog.created_at < cutoff_date)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount
