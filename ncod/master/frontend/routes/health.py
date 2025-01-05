"""Health模块"""

import time
from typing import Any, Dict

import psutil
from config import settings
from database.db import db_manager, get_db
from fastapi import APIRouter, Depends, HTTPException
from prometheus_client import Counter, Histogram, generate_latest
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/health", tags=["health"])

# Prometheus metrics
REQUEST_COUNT = Counter(
    "ncod_request_total", "Total request count", ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "ncod_request_latency_seconds", "Request latency in seconds", ["method", "endpoint"]
)


async def check_database(db: AsyncSession) -> Dict[str, Any]:
    """检查数据库连接状态"""
    try:
        # 执行简单查询
        await db.execute("SELECT 1")
        pool_status = await db_manager.get_pool_status()
        return {"status": "healthy", "pool": pool_status}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_redis() -> Dict[str, Any]:
    """检查Redis连接状态"""
    try:
        redis = await aioredis.from_url(settings.REDIS_URL)
        await redis.ping()
        info = await redis.info()
        await redis.close()
        return {
            "status": "healthy",
            "used_memory": info["used_memory_human"],
            "connected_clients": info["connected_clients"],
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def get_system_stats() -> Dict[str, Any]:
    """获取系统资源使用情况"""
    return {
        "cpu": {"percent": psutil.cpu_percent(interval=1), "count": psutil.cpu_count()},
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent,
        },
        "disk": {
            "total": psutil.disk_usage("/").total,
            "used": psutil.disk_usage("/").used,
            "free": psutil.disk_usage("/").free,
            "percent": psutil.disk_usage("/").percent,
        },
    }


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """存活检查"""
    return {"status": "alive"}


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """就绪检查"""
    start_time = time.time()

    # 检查数据库
    db_status = await check_database(db)
    if db_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=db_status)

    # 检查Redis
    redis_status = await check_redis()
    if redis_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=redis_status)

    latency = time.time() - start_time
    REQUEST_LATENCY.labels(method="GET", endpoint="/health/ready").observe(latency)

    return {
        "status": "ready",
        "database": db_status,
        "redis": redis_status,
        "latency": f"{latency:.3f}s",
    }


@router.get("/status")
async def system_status(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """系统状态检查"""
    start_time = time.time()

    # 获取所有组件状态
    db_status = await check_database(db)
    redis_status = await check_redis()
    system_stats = get_system_stats()

    latency = time.time() - start_time
    REQUEST_LATENCY.labels(method="GET", endpoint="/health/status").observe(latency)

    return {
        "timestamp": time.time(),
        "database": db_status,
        "redis": redis_status,
        "system": system_stats,
        "latency": f"{latency:.3f}s",
    }


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()
