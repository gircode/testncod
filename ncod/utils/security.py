"""安全工具模块"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from ncod.utils.config import settings
from ncod.utils.logger import logger

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """令牌数据模型"""

    sub: str
    exp: datetime
    type: str = "access"
    scopes: list[str] = []


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        bool: 密码是否匹配
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """获取密码哈希值

    Args:
        password: 明文密码

    Returns:
        str: 密码哈希值
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise ValueError("Failed to hash password") from e


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌

    Args:
        data: 令牌数据
        expires_delta: 过期时间

    Returns:
        str: JWT令牌
    """
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            expires_delta
            if expires_delta
            else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        token_data = TokenData(**to_encode)
        encoded_jwt = jwt.encode(
            token_data.model_dump(),
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise ValueError("Failed to create access token") from e


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证令牌

    Args:
        token: JWT令牌

    Returns:
        Optional[Dict[str, Any]]: 令牌数据
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenData(**payload)
        return token_data.model_dump()
    except jwt.PyJWTError as e:
        logger.error(f"Token verification error: {e}")
        return None
    except Exception as e:
        logger.error(f"Token data validation error: {e}")
        return None


def generate_device_signature(device_id: str, timestamp: Union[str, datetime]) -> str:
    """生成设备签名

    Args:
        device_id: 设备ID
        timestamp: 时间戳

    Returns:
        str: 设备签名
    """
    try:
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()
        message = f"{device_id}:{timestamp}"
        signature = hmac.new(
            settings.JWT_SECRET_KEY.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return signature
    except Exception as e:
        logger.error(f"Device signature generation error: {e}")
        raise ValueError("Failed to generate device signature") from e


def verify_device_signature(
    device_id: str, timestamp: Union[str, datetime], signature: str
) -> bool:
    """验证设备签名

    Args:
        device_id: 设备ID
        timestamp: 时间戳
        signature: 设备签名

    Returns:
        bool: 签名是否有效
    """
    try:
        expected_signature = generate_device_signature(device_id, timestamp)
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Device signature verification error: {e}")
        return False
