import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# 导入所有模型以便Alembic可以检测
from ncod.master.models.user import User
from ncod.master.models.mac_address import MacAddress
from ncod.master.models.device import Device
from ncod.master.models.slave import Slave
from ncod.master.models.metrics import DeviceMetrics, SlaveMetrics
from ncod.master.database import Base

# 读取配置
config = context.config

# 如果配置中有section，则设置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加MetaData对象，包含所有要迁移的表
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """在"离线"模式下运行迁移。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在异步环境中运行迁移。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在"在线"模式下运行迁移。"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
