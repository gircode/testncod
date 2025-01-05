"""认证中间件"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError

from ncod.core.db.base import get_db
from ncod.core.security import decode_token
from ncod.models.user import User
from ncod.utils.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> dict:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
        }
    except JWTError:
        logger.error("Token解析失败", exc_info=True)
        raise credentials_exception
    except Exception as e:
        logger.error(f"获取当前用户失败: {str(e)}", exc_info=True)
        raise credentials_exception
