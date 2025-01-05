import typer
import asyncio
from sqlalchemy.orm import Session

from ncod.core.db.database import SessionLocal
from ncod.master.services.cache_manager import cache_manager
from ncod.master.services.cache_warmup import CacheWarmupService

app = typer.Typer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.command()
def warmup():
    """预热缓存"""
    db = next(get_db())
    warmup_service = CacheWarmupService(db, cache_manager)
    asyncio.run(warmup_service.warmup_all())


@app.command()
def clear(cache_type: str = None):
    """清理缓存

    Args:
        cache_type: 缓存类型(short/long/stats/session/all)
    """
    if cache_type and cache_type not in ["short", "long", "stats", "session", "all"]:
        typer.echo("Invalid cache type")
        raise typer.Exit(1)

    if cache_type == "all" or not cache_type:
        cache_manager.clear_all()
        typer.echo("All caches cleared")
    else:
        cache = cache_manager._get_cache(cache_type)
        if cache:
            cache.clear()
            typer.echo(f"{cache_type} cache cleared")


@app.command()
def stats():
    """显示缓存统计"""
    metrics = cache_manager.get_metrics()

    typer.echo("\nCache Statistics:")
    typer.echo("-" * 40)
    typer.echo(f"Total Requests: {metrics['total_requests']}")
    typer.echo(f"Hit Rate: {metrics['hit_rate']}%")
    typer.echo(f"Memory Usage: {metrics['memory_usage']} bytes")
    typer.echo(f"Average Access Time: {metrics['avg_access_time']}ms")

    typer.echo("\nCache Type Statistics:")
    typer.echo("-" * 40)
    for cache_type, stats in metrics["type_stats"].items():
        typer.echo(f"\n{cache_type}:")
        typer.echo(f"  Hits: {stats['hits']}")
        typer.echo(f"  Misses: {stats['misses']}")
        typer.echo(f"  Hit Rate: {stats['hit_rate']}%")
