"""
从服务器入口
"""

import asyncio
import logging

import aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache2 import FastAPICache
from fastapi_cache2.backends.redis import RedisBackend

from .api.v1.api import api_router
from .core.config import settings
from .db.session import async_session
from .services.monitor import MonitorService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NCOD Slave",
    description="NCOD从服务器",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# 配置CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 注册路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 监控服务实例
monitor_service = None


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    try:
        # 初始化Redis缓存
        redis = aioredis.from_url(
            settings.REDIS_URL, encoding="utf8", decode_responses=True
        )
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

        # 初始化监控服务
        global monitor_service
        db = async_session()
        monitor_service = MonitorService(db)
        await monitor_service.start()

        logger.info("服务启动成功")

    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    try:
        # 停止监控服务
        if monitor_service:
            await monitor_service.stop()

        # 关闭缓存
        await FastAPICache.clear()

        logger.info("服务关闭成功")

    except Exception as e:
        logger.error(f"服务关闭失败: {str(e)}")
        raise


@app.get("/")
async def root():
    """根路由"""
    return {"message": "Welcome to NCOD Slave Server", "version": "1.0.0"}
