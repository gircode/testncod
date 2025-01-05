"""
API路由注册
"""

from fastapi import APIRouter

from .endpoints import auth, data, health, monitor, registration

api_router = APIRouter()

# 注册认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 注册健康检查路由
api_router.include_router(health.router, prefix="/health", tags=["health"])

# 注册监控路由
api_router.include_router(monitor.router, prefix="/monitor", tags=["monitor"])

# 注册数据管理路由
api_router.include_router(data.router, prefix="/data", tags=["data"])

# 注册用户注册路由
api_router.include_router(
    registration.router, prefix="/registration", tags=["registration"]
)
