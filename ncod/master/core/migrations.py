"""数据库迁移模块"""

import asyncio
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine

from ncod.utils.config import settings
from ncod.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_alembic_config(engine: Optional[AsyncEngine] = None) -> Config:
    """获取Alembic配置

    Args:
        engine: SQLAlchemy异步引擎实例

    Returns:
        Config: Alembic配置对象
    """
    # 获取migrations目录路径
    migrations_dir = Path(__file__).parent / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)

    # 创建配置对象
    config = Config()
    config.set_main_option("script_location", str(migrations_dir))
    config.set_main_option("sqlalchemy.url", settings.DB_URL)

    if engine:
        config.attributes["connection"] = engine

    return config


async def init_database():
    """初始化数据库"""
    try:
        config = get_alembic_config()
        command.init(config, "migrations")
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def create_migration(message: str):
    """创建数据库迁移

    Args:
        message: 迁移说明信息
    """
    try:
        config = get_alembic_config()
        command.revision(config, message=message, autogenerate=True)
        logger.info(f"创建数据库迁移成功: {message}")
    except Exception as e:
        logger.error(f"创建数据库迁移失败: {e}")
        raise


async def upgrade_database(revision: str = "head"):
    """升级数据库

    Args:
        revision: 目标版本，默认为最新版本
    """
    try:
        config = get_alembic_config()
        command.upgrade(config, revision)
        logger.info(f"数据库升级成功: {revision}")
    except Exception as e:
        logger.error(f"数据库升级失败: {e}")
        raise


async def downgrade_database(revision: str):
    """降级数据库

    Args:
        revision: 目标版本
    """
    try:
        config = get_alembic_config()
        command.downgrade(config, revision)
        logger.info(f"数据库降级成功: {revision}")
    except Exception as e:
        logger.error(f"数据库降级失败: {e}")
        raise
