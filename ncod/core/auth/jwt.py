"""JWT认证处理"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt
from passlib.context import CryptContext
from ncod.core.config import config

# 创建密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> Dict[str, Any]:
    """解码令牌"""
    try:
        return jwt.decode(token, config.jwt_secret, algorithms=["HS256"])
    except jwt.JWTError:
        raise ValueError("Invalid token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)
