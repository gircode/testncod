"""
令牌管理模块
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.exceptions import AuthenticationError, SecurityError
from jose import JWTError, jwt


class TokenType(Enum):
    """令牌类型"""

    ACCESS = "access"  # 短期访问令牌（Web页面使用）
    REFRESH = "refresh"  # 刷新令牌
    DEVICE = "device"  # 设备令牌（永久有效，直到设备断开连接）
    CLIENT = "client"  # 客户端令牌（可自动续期）
    WEB = "web"  # Web令牌（一次性会话）


class TokenStatus(Enum):
    """令牌状态"""

    ACTIVE = "active"  # 活跃状态
    EXPIRED = "expired"  # 已过期
    REVOKED = "revoked"  # 已撤销
    PENDING_RENEWAL = "pending_renewal"  # 等待续期


class TokenInfo:
    """令牌信息"""

    def __init__(
        self,
        token: str,
        token_type: TokenType,
        user_id: str,
        expires_at: datetime,
        status: TokenStatus = TokenStatus.ACTIVE,
        last_activity: Optional[datetime] = None,
        device_id: Optional[str] = None,
    ):
        self.token = token
        self.token_type = token_type
        self.user_id = user_id
        self.expires_at = expires_at
        self.status = status
        self.last_activity = last_activity or datetime.now()
        self.device_id = device_id


def create_token(
    subject: Any,
    token_type: TokenType = TokenType.ACCESS,
    expires_delta: Optional[timedelta] = None,
    device_id: Optional[str] = None,
) -> str:
    """创建令牌

    Args:
        subject: 令牌主体（通常是用户ID）
        token_type: 令牌类型
        expires_delta: 自定义过期时间
        device_id: 设备ID（用于设备令牌）

    Returns:
        str: 令牌
    """
    if not expires_delta:
        if token_type == TokenType.ACCESS:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        elif token_type == TokenType.REFRESH:
            expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        elif token_type == TokenType.DEVICE:
            expires_delta = timedelta(days=36500)  # 100年，实际上永久有效
        elif token_type == TokenType.CLIENT:
            expires_delta = timedelta(hours=settings.CLIENT_TOKEN_EXPIRE_HOURS)
        elif token_type == TokenType.WEB:
            expires_delta = timedelta(minutes=settings.WEB_SESSION_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta
    to_encode = {"exp": expire, "sub": str(subject), "type": token_type.value}

    if device_id:
        to_encode["device_id"] = device_id

    try:
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        raise SecurityError(message="创建令牌失败", details={"error": str(e)})


def verify_token(token: str, expected_type: Optional[TokenType] = None) -> dict:
    """验证令牌

    Args:
        token: 令牌
        expected_type: 预期的令牌类型

    Returns:
        dict: 令牌数据

    Raises:
        AuthenticationError: 令牌无效或已过期
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # 验证令牌类型
        if expected_type:
            token_type = payload.get("type")
            if not token_type or token_type != expected_type.value:
                raise AuthenticationError("令牌类型不匹配")

        return payload
    except JWTError as e:
        raise AuthenticationError("无效的令牌") from e
