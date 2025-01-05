from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ncod.core.db.database import SessionLocal
from ncod.master.services.device_stats import DeviceStatsService


async def cleanup_old_stats():
    """清理旧的统计数据"""
    with SessionLocal() as db:
        stats_service = DeviceStatsService(db)
        await stats_service.cleanup_old_stats()


def setup_stats_cleanup():
    """设置统计数据清理任务"""
    scheduler = AsyncIOScheduler()

    # 每天凌晨运行清理任务
    scheduler.add_job(cleanup_old_stats, "cron", hour=0, minute=0)

    scheduler.start()
