import asyncio
import click
import uvicorn
from pathlib import Path

from ncod.utils.config import settings
from ncod.utils.logger import setup_logger
from ncod.master.core.migrations import (
    init_database,
    create_migration,
    upgrade_database,
    downgrade_database,
)

logger = setup_logger(__name__)


@click.group()
def cli():
    """NCOD - Network Connected Open Device CLI"""
    pass


@cli.group()
def server():
    """管理主服务器"""
    pass


@server.command()
@click.option("--host", default="0.0.0.0", help="服务器监听地址")
@click.option("--port", default=8000, help="服务器监听端口")
@click.option("--reload", is_flag=True, help="启用热重载")
def start_server(host: str, port: int, reload: bool):
    """启动主服务器"""
    logger.info(f"启动主服务器 {host}:{port}")
    uvicorn.run(
        "ncod.master.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.LOG_LEVEL.lower(),
    )


@cli.group()
def slave():
    """管理从服务器"""
    pass


@slave.command()
@click.option("--host", default="0.0.0.0", help="服务器监听地址")
@click.option("--port", default=5000, help="服务器监听端口")
@click.option("--master", default="http://localhost:8000", help="主服务器地址")
def start_slave(host: str, port: int, master: str):
    """启动从服务器"""
    logger.info(f"启动从服务器 {host}:{port}")
    logger.info(f"连接主服务器 {master}")
    uvicorn.run(
        "ncod.slave.app:app", host=host, port=port, log_level=settings.LOG_LEVEL.lower()
    )


@cli.group()
def device():
    """设备管理"""
    pass


@device.command()
def list():
    """列出所有设备"""
    # TODO: 实现设备列表查询
    pass


@device.command()
@click.argument("device_id")
def info(device_id: str):
    """查看设备详情"""
    # TODO: 实现设备详情查询
    pass


@device.command()
@click.argument("device_id")
def connect(device_id: str):
    """连接设备"""
    # TODO: 实现设备连接
    pass


@device.command()
@click.argument("device_id")
def disconnect(device_id: str):
    """断开设备连接"""
    # TODO: 实现设备断开连接
    pass


@cli.group()
def db():
    """数据库管理"""
    pass


@db.command()
def init():
    """初始化数据库"""
    asyncio.run(init_database())


@db.command()
@click.option("--message", "-m", required=True, help="迁移说明信息")
def migrate(message: str):
    """创建数据库迁移"""
    asyncio.run(create_migration(message))


@db.command()
@click.option("--revision", default="head", help="目标版本")
def upgrade(revision: str):
    """升级数据库"""
    asyncio.run(upgrade_database(revision))


@db.command()
@click.argument("revision")
def downgrade(revision: str):
    """降级数据库"""
    asyncio.run(downgrade_database(revision))


def main():
    cli()
