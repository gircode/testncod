"""安全相关工具"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt
from passlib.context import CryptContext
from ncod.config.settings import Settings
from sqlalchemy.orm import Session

settings = Settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """解码令牌"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def verify_mac_address(user_id: int, mac_address: str) -> bool:
    # 实现MAC地址验证逻辑
    return True  # 临时返回True，需要根据实际需求实现


def register_mac_address(user_id: int, mac_address: str) -> None:
    # 实现MAC地址注册逻辑
    pass
