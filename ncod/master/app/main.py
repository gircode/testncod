"""
主程序
"""

import logging

import aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache2 import FastAPICache
from fastapi_cache2.backends.redis import RedisBackend

from .api.v1.api import api_router
from .core.config import settings
from .db.init_db import init_db
from .db.session import get_db
from .services.monitor import MonitorService

# 配置日志
logging.basicConfig(level=settings.LOG_LEVEL, format=settings.LOG_FORMAT)

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    try:
        # 初始化数据库
        await init_db()
        logger.info("数据库初始化完成")

        # 初始化Redis缓存
        redis = aioredis.from_url(
            settings.REDIS_URL, encoding="utf8", decode_responses=True
        )
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        logger.info("Redis缓存初始化完成")

        # 启动监控服务
        async for db in get_db():
            monitor_service = MonitorService(db)
            await monitor_service.start()
            logger.info("监控服务启动完成")
            break

    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    try:
        # 停止监控服务
        async for db in get_db():
            monitor_service = MonitorService(db)
            await monitor_service.stop()
            logger.info("监控服务已停止")
            break

    except Exception as e:
        logger.error(f"关闭失败: {str(e)}")
        raise
