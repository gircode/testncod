"""
登录历史记录服务
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.user import LoginHistory, User


class LoginHistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_login_attempt(
        self,
        user_id: int,
        success: bool,
        ip_address: str,
        user_agent: str,
        error_message: Optional[str] = None,
    ) -> LoginHistory:
        """
        记录登录尝试
        """
        login_history = LoginHistory(
            user_id=user_id,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message,
        )
        self.db.add(login_history)
        await self.db.commit()
        await self.db.refresh(login_history)
        return login_history

    async def get_user_login_history(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        success: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[List[LoginHistory], int]:
        """
        获取用户登录历史
        """
        query = select(LoginHistory).where(LoginHistory.user_id == user_id)

        if success is not None:
            query = query.where(LoginHistory.success == success)

        if start_date:
            query = query.where(LoginHistory.created_at >= start_date)

        if end_date:
            query = query.where(LoginHistory.created_at <= end_date)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        # 获取分页数据
        query = query.order_by(LoginHistory.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        history = result.scalars().all()

        return history, total

    async def is_user_locked(self, user_id: int) -> bool:
        """
        检查用户是否被锁定
        """
        # 获取最近失败的登录尝试
        failed_attempts = await self.get_recent_failed_attempts(user_id)
        return len(failed_attempts) >= settings.MAX_LOGIN_ATTEMPTS

    async def get_recent_failed_attempts(self, user_id: int) -> List[LoginHistory]:
        """
        获取最近失败的登录尝试
        """
        lockout_period = datetime.utcnow() - timedelta(
            minutes=settings.LOGIN_LOCKOUT_MINUTES
        )
        query = (
            select(LoginHistory)
            .where(
                LoginHistory.user_id == user_id,
                LoginHistory.success == False,
                LoginHistory.created_at >= lockout_period,
            )
            .order_by(LoginHistory.created_at.desc())
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def cleanup_old_records(self, days: int) -> int:
        """
        清理旧的登录历史记录
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = delete(LoginHistory).where(LoginHistory.created_at < cutoff_date)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount
