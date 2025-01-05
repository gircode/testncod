"""API路由配置"""

from fastapi import APIRouter

from .endpoints import auth, user, device

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户相关路由
api_router.include_router(user.router, prefix="/users", tags=["用户"])

# 设备相关路由
api_router.include_router(device.router, prefix="/devices", tags=["设备"])
