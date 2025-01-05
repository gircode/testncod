"""
健康检查路由
"""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi_cache2.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import settings
from ....db.session import get_db
from ....deps import get_current_active_user
from ....services.health import HealthService

router = APIRouter()


@router.get("/check")
@cache(expire=30)
async def check_health(db: AsyncSession = Depends(get_db)) -> Any:
    """检查系统健康状态"""
    health_service = HealthService(db)
    return await health_service.check()


@router.get("/summary")
@cache(expire=60)
async def get_system_summary(
    db: AsyncSession = Depends(get_db), _: Any = Depends(get_current_active_user)
) -> Any:
    """获取系统概要信息"""
    health_service = HealthService(db)
    return await health_service.get_system_summary()
