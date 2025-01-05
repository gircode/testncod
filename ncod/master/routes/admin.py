from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from ncod.master.auth import get_current_user, require_admin
from ncod.master.services.cache_manager import cache_manager
from ncod.master.services.cache_warmup import CacheWarmupService
from sqlalchemy.orm import Session
from ncod.core.db.database import get_db

router = APIRouter(prefix="/api/v1/admin", tags=["系统管理"])


@router.get("/cache/metrics")
@require_admin
async def get_cache_metrics(current_user=Depends(get_current_user)):
    """获取缓存指标"""
    return cache_manager.get_metrics()


@router.get("/cache/history")
@require_admin
async def get_cache_metrics_history(current_user=Depends(get_current_user)):
    """获取缓存指标历史"""
    return cache_manager.get_metrics_history()


@router.post("/cache/warmup")
@require_admin
async def warmup_cache(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """预热缓存"""
    warmup_service = CacheWarmupService(db, cache_manager)
    background_tasks.add_task(warmup_service.warmup_all)
    return {"message": "Cache warmup started"}


@router.post("/cache/clear/{cache_type}")
@require_admin
async def clear_cache(cache_type: str, current_user=Depends(get_current_user)):
    """清理缓存"""
    if cache_type not in ["short", "long", "stats", "session", "all"]:
        raise HTTPException(status_code=400, detail="Invalid cache type")

    if cache_type == "all":
        cache_manager.clear_all()
    else:
        cache = cache_manager._get_cache(cache_type)
        if cache:
            cache.clear()

    return {"message": f"{cache_type} cache cleared"}


@router.get("/cache/warmup/status")
@require_admin
async def get_warmup_status(current_user=Depends(get_current_user)):
    """获取缓存预热状态"""
    if not hasattr(cache_manager, "warmup_service"):
        return {"status": "not_started"}

    progress = cache_manager.warmup_service.progress
    return {
        "status": "in_progress" if progress.total > progress.completed else "completed",
        **progress.to_dict(),
    }
