from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from ..models.user import User, UserStatus
from ..core.exceptions import AuthenticationError
import os

# 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """验证用户"""
    user = await User.get_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await User.get_by_username(username)
    if user is None:
        raise credentials_exception

    if user.status != UserStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is not approved"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if current_user.status == UserStatus.DISABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have admin privileges",
        )
    return current_user


async def verify_mac_address(user: User, mac_address: str) -> bool:
    """验证MAC地址"""
    try:
        user_macs = await user.get_mac_addresses()
        return any(mac.address == mac_address and mac.is_active for mac in user_macs)
    except Exception as e:
        raise AuthenticationError(f"Error verifying MAC address: {str(e)}")


async def authenticate_with_mac(username: str, mac_address: str) -> Optional[User]:
    """使用MAC地址进行认证"""
    try:
        user = await User.get_by_username(username)
        if not user or user.status != UserStatus.APPROVED:
            return None

        if not await verify_mac_address(user, mac_address):
            return None

        return user

    except Exception as e:
        raise AuthenticationError(f"Error authenticating with MAC address: {str(e)}")


def create_user_token(user: User) -> Dict[str, Any]:
    """创建用户令牌"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict(),
    }
