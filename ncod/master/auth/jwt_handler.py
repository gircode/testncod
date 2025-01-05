"""JWT认证处理"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from ..core.config import config


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.jwt_secret, algorithm="HS256")
