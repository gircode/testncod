"""API路由注册"""

from fastapi import FastAPI
from .device import router as device_router
from .slave import router as slave_router
from .user import router as user_router
from .monitor import router as monitor_router


def register_routes(app: FastAPI):
    """注册所有路由"""
    app.include_router(device_router, prefix="/api/v1/devices", tags=["devices"])
    app.include_router(slave_router, prefix="/api/v1/slaves", tags=["slaves"])
    app.include_router(user_router, prefix="/api/v1/users", tags=["users"])
    app.include_router(monitor_router, prefix="/api/v1/monitor", tags=["monitor"])
