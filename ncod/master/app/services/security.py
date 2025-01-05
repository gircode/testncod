"""
安全服务模块
"""

import base64
import ipaddress
import re
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, List, Optional

import pyotp
import qrcode
from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.cache import RedisCache
from ..core.config import settings
from ..models.login_history import LoginHistory
from ..models.user import User


class SecurityService:
    def __init__(self, db: AsyncSession, cache: RedisCache):
        self.db = db
        self.cache = cache

    async def check_password_strength(self, password: str) -> Dict[str, bool]:
        """检查密码强度"""
        checks = {
            "length": len(password) >= settings.PASSWORD_MIN_LENGTH,
            "uppercase": (
                bool(re.search(r"[A-Z]", password))
                if settings.PASSWORD_REQUIRE_UPPERCASE
                else True
            ),
            "lowercase": (
                bool(re.search(r"[a-z]", password))
                if settings.PASSWORD_REQUIRE_LOWERCASE
                else True
            ),
            "digits": (
                bool(re.search(r"\d", password))
                if settings.PASSWORD_REQUIRE_DIGITS
                else True
            ),
            "special": (
                bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
                if settings.PASSWORD_REQUIRE_SPECIAL
                else True
            ),
        }
        return checks

    async def validate_password(self, password: str) -> None:
        """验证密码强度"""
        checks = await self.check_password_strength(password)
        if not all(checks.values()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet requirements",
                    "checks": checks,
                },
            )

    async def check_ip_whitelist(self, ip_address: str) -> bool:
        """检查IP是否在白名单中"""
        if not settings.IP_WHITELIST:
            return True

        client_ip = ipaddress.ip_address(ip_address)
        return any(
            client_ip in ipaddress.ip_network(allowed_ip)
            for allowed_ip in settings.IP_WHITELIST
        )

    async def setup_2fa(self, user: User) -> str:
        """设置双因素认证"""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # 生成二维码
        provisioning_uri = totp.provisioning_uri(
            user.email, issuer_name=settings.PROJECT_NAME
        )
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        # 保存密钥
        await self.cache.set(f"2fa_setup_{user.id}", secret, expire=1800)  # 30分钟过期

        return qr_code

    async def verify_2fa(self, user: User, code: str) -> bool:
        """验证双因素认证码"""
        if not user.is_2fa_enabled:
            return True

        totp = pyotp.TOTP(user.totp_secret)
        return totp.verify(code)

    async def get_login_statistics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict:
        """获取登录统计信息"""
        query = select(LoginHistory)

        if start_date:
            query = query.where(LoginHistory.created_at >= start_date)
        if end_date:
            query = query.where(LoginHistory.created_at <= end_date)

        result = await self.db.execute(query)
        login_attempts = result.scalars().all()

        total_attempts = len(login_attempts)
        successful_attempts = sum(1 for attempt in login_attempts if attempt.success)

        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": (
                (successful_attempts / total_attempts * 100)
                if total_attempts > 0
                else 0
            ),
            "failed_attempts": total_attempts - successful_attempts,
        }

    async def detect_anomalies(self, user: User, ip_address: str) -> List[str]:
        """检测异常行为"""
        anomalies = []

        # 检查不常用IP
        query = select(LoginHistory).where(
            and_(
                LoginHistory.user_id == user.id,
                LoginHistory.success == True,
                LoginHistory.created_at >= datetime.utcnow() - timedelta(days=30),
            )
        )
        result = await self.db.execute(query)
        recent_logins = result.scalars().all()

        used_ips = set(login.ip_address for login in recent_logins)
        if ip_address not in used_ips and recent_logins:
            anomalies.append("Unusual IP address")

        # 检查短时间内的多次失败
        recent_failures = [
            login
            for login in recent_logins
            if not login.success
            and login.created_at >= datetime.utcnow() - timedelta(minutes=30)
        ]
        if len(recent_failures) >= 3:
            anomalies.append("Multiple failed attempts")

        # 检查非常规时间登录
        current_hour = datetime.utcnow().hour
        if current_hour < 6 or current_hour > 22:
            anomalies.append("Unusual login time")

        return anomalies

    async def analyze_user_activity(self, user: User) -> Dict:
        """分析用户活动"""
        query = select(LoginHistory).where(LoginHistory.user_id == user.id)
        result = await self.db.execute(query)
        login_history = result.scalars().all()

        # 分析登录时间分布
        hour_distribution = {i: 0 for i in range(24)}
        for login in login_history:
            hour = login.created_at.hour
            hour_distribution[hour] += 1

        # 分析常用IP
        ip_frequency = {}
        for login in login_history:
            ip_frequency[login.ip_address] = ip_frequency.get(login.ip_address, 0) + 1

        # 计算成功率趋势
        success_trend = []
        current_date = datetime.utcnow()
        for i in range(7):
            date = current_date - timedelta(days=i)
            day_logins = [
                login
                for login in login_history
                if login.created_at.date() == date.date()
            ]
            success_rate = (
                sum(1 for login in day_logins if login.success) / len(day_logins) * 100
                if day_logins
                else 0
            )
            success_trend.append(
                {"date": date.date().isoformat(), "success_rate": success_rate}
            )

        return {
            "hour_distribution": hour_distribution,
            "top_ips": sorted(ip_frequency.items(), key=lambda x: x[1], reverse=True)[
                :5
            ],
            "success_trend": success_trend,
        }

    async def audit_log(
        self, user_id: int, action: str, status: str, details: Optional[Dict] = None
    ) -> None:
        """记录安全审计日志"""
        # 实现审计日志记录逻辑
        pass
