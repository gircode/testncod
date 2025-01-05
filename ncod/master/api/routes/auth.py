"""认证路由"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.core.auth.jwt_handler import create_access_token
from ncod.master.services.user import UserService
from ncod.master.schemas.auth import LoginRequest, LoginResponse, Token

router = APIRouter()
user_service = UserService()
logger = setup_logger("auth_routes")


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """用户登录"""
    try:
        # 获取用户
        user = await user_service.get_user_by_username(login_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        # 验证密码
        if not user_service.verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        # 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        # 创建访问令牌
        token_data = {
            "sub": user.id,
            "username": user.username,
            "organization_id": user.organization_id,
        }
        access_token = create_access_token(user.id, additional_data=token_data)

        # 更新最后登录时间
        await user_service.update_last_login(user.id)

        return LoginResponse(
            token=Token(access_token=access_token, token_type="bearer"), user=user
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2兼容的令牌获取"""
    try:
        # 获取用户
        user = await user_service.get_user_by_username(form_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 验证密码
        if not user_service.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        # 创建访问令牌
        token_data = {
            "sub": user.id,
            "username": user.username,
            "organization_id": user.organization_id,
        }
        access_token = create_access_token(user.id, additional_data=token_data)

        # 更新最后登录时间
        await user_service.update_last_login(user.id)

        return Token(access_token=access_token, token_type="bearer")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate token",
        )
