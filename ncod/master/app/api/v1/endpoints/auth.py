"""
认证路由
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import settings
from ....db.session import get_db
from ....deps import get_current_active_user
from ....models.auth import User
from ....services.auth import AuthService

router = APIRouter()


class Token(BaseModel):
    """令牌"""

    access_token: str
    token_type: str


class UserInfo(BaseModel):
    """用户信息"""

    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    admin_level: int
    department_id: int | None = None
    group_id: int | None = None

    class Config:
        from_attributes = True


@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """用户登录"""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(
        username=form_data.username, password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/client", response_model=Token)
async def login_client(
    *,
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
    mac_address: str,
) -> Any:
    """客户端登录"""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(
        username=form_data.username,
        password=form_data.password,
        mac_address=mac_address,
        client_type="client",
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: User = Depends(get_current_active_user)) -> Any:
    """获取当前用户信息"""
    return current_user
