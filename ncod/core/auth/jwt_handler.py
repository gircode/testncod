"""JWT处理模块"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from ncod.core.config import config
from ncod.core.logger import auth_logger as logger

# JWT配置
SECRET_KEY = str(config.jwt.secret_key)
ALGORITHM = str(config.jwt.algorithm)
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.jwt.access_token_expire_minutes)


def create_jwt_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建JWT令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating JWT token: {e}")
        raise


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """解码JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Error decoding JWT token: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error decoding JWT token: {e}")
        raise


def create_access_token(
    user_id: str, additional_data: Optional[Dict[str, Any]] = None
) -> str:
    """创建访问令牌"""
    data = {"sub": user_id, "type": "access"}
    if additional_data:
        data.update(additional_data)

    return create_jwt_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """验证JWT令牌"""
    try:
        payload = decode_jwt_token(token)
        # 验证令牌类型
        if payload.get("type") != "access":
            return None
        # 验证过期时间
        exp = payload.get("exp")
        if not exp or datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None
        return payload
    except Exception as e:
        logger.error(f"Error verifying JWT token: {e}")
        return None
