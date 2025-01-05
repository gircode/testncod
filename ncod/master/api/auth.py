"""认证API"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from ncod.master.services.auth import auth_service
from ncod.core.logger import setup_logger
from ncod.master.middleware.auth import get_current_user

logger = setup_logger("auth_api")
router = APIRouter(prefix="/api/v1/auth")
security = HTTPBearer()


class LoginRequest(BaseModel):
    """登录请求"""

    username: str
    password: str


class MacLoginRequest(BaseModel):
    """MAC地址登录请求"""

    mac_address: str


class RefreshRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str


@router.post("/login")
async def login(request: LoginRequest):
    """用户登录"""
    try:
        success, message, data = await auth_service.authenticate(
            request.username, request.password
        )
        if not success:
            raise HTTPException(status_code=401, detail=message)
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/login/mac")
async def login_mac(request: MacLoginRequest):
    """MAC地址登录"""
    try:
        success, message, data = await auth_service.authenticate_mac(
            request.mac_address
        )
        if not success:
            raise HTTPException(status_code=401, detail=message)
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in MAC login: {e}")
        raise HTTPException(status_code=500, detail="MAC login failed")


@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """刷新令牌"""
    try:
        success, message, data = await auth_service.refresh_token(request.refresh_token)
        if not success:
            raise HTTPException(status_code=401, detail=message)
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return user


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """用户登出"""
    # 这里可以添加令牌黑名单等逻辑
    return {"message": "Logged out successfully"}
