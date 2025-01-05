"""
数据管理路由
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import settings
from ....db.session import get_db
from ....deps import get_current_admin_user
from ....services.data_manager import DataManager

router = APIRouter()


@router.post("/cleanup")
async def cleanup_data(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(get_current_admin_user),
) -> Any:
    """清理旧数据"""
    data_manager = DataManager(db)
    background_tasks.add_task(data_manager.cleanup_old_data)
    return {"message": "数据清理任务已启动"}


@router.post("/archive")
async def archive_data(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(get_current_admin_user),
) -> Any:
    """归档数据"""
    data_manager = DataManager(db)
    archive_before = datetime.utcnow() - timedelta(days=settings.DATA_RETENTION_DAYS)
    background_tasks.add_task(data_manager.archive_data, archive_before)
    return {"message": "数据归档任务已启动"}


@router.post("/optimize")
async def optimize_tables(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(get_current_admin_user),
) -> Any:
    """优化数据表"""
    data_manager = DataManager(db)
    background_tasks.add_task(data_manager.optimize_tables)
    return {"message": "数据表优化任务已启动"}


@router.get("/stats")
async def get_storage_stats(
    db: AsyncSession = Depends(get_db), _: Any = Depends(get_current_admin_user)
) -> Any:
    """获取存储统计信息"""
    data_manager = DataManager(db)
    return await data_manager.get_storage_stats()
