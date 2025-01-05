"""
API路由
"""

from fastapi import APIRouter

from .endpoints import device, health, monitor, sync

api_router = APIRouter()

# 设备管理
api_router.include_router(device.router, prefix="/devices", tags=["devices"])

# 监控管理
api_router.include_router(monitor.router, prefix="/monitor", tags=["monitor"])

# 健康检查
api_router.include_router(health.router, prefix="/health", tags=["health"])

# 数据同步
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
