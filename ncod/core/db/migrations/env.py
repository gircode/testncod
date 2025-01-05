"""数据库迁移环境配置"""

import asyncio
import logging
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from ncod.core.config import config as app_config
from ncod.core.db.base import Base

logger = logging.getLogger("migrations")

# 读取alembic配置
config = context.config

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据
target_metadata = Base.metadata


def get_url():
    """获取数据库URL"""
    return app_config.database_write_url


def run_migrations_offline() -> None:
    """离线运行迁移"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """在线运行迁移"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移"""
    context.configure(
        connection=connection, target_metadata=target_metadata, compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_async_migrations() -> None:
    """运行异步迁移"""
    asyncio.run(run_migrations_online())


if context.is_offline_mode():
    logger.info("Running migrations offline")
    run_migrations_offline()
else:
    logger.info("Running migrations online")
    run_async_migrations()
