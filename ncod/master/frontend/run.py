"""Run模块"""

import logging
import os
import sys
from pathlib import Path

import click
import uvicorn
from alembic import command
from alembic.config import Config
from config import get_settings, settings

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

# 配置日志
logger = logging.getLogger(__name__)


def setup_alembic():
    """配置Alembic"""
    try:
        config = Config(settings.ALEMBIC_CONFIG)
        config.set_main_option("script_location", "database/migrations")
        config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        return config
    except Exception as e:
        logger.error(f"Failed to setup Alembic: {e}")
        raise


def run_migrations(alembic_cfg):
    """运行数据库迁移"""
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        raise


def create_required_directories():
    """创建必要的目录"""
    dirs = [
        settings.BASE_DIR / "logs",
        settings.BASE_DIR / "static",
        settings.BASE_DIR / "templates",
        settings.BASE_DIR / "uploads",
    ]

    for dir_path in dirs:
        dir_path.mkdir(exist_ok=True)
        logger.info(f"Created directory: {dir_path}")


@click.group()
def cli():
    """Master Server管理工具"""
    pass


@cli.command()
@click.option("--host", default=None, help="绑定的主机地址")
@click.option("--port", default=None, type=int, help="监听的端口")
@click.option("--workers", default=None, type=int, help="工作进程数")
@click.option("--reload", is_flag=True, help="是否启用热重载")
@click.option("--env", default=None, help="环境配置文件")
def runserver(host, port, workers, reload, env):
    """运行服务器"""
    try:
        # 加载环境配置
        if env:
            os.environ["ENV_FILE"] = env
            settings = get_settings()

        # 创建必要的目录
        create_required_directories()

        # 设置日志系统
        settings.setup_logging()

        # 运行数据库迁移
        alembic_cfg = setup_alembic()
        run_migrations(alembic_cfg)

        # 启动服务器
        uvicorn.run(
            "main:app",
            host=host or settings.HOST,
            port=port or settings.PORT,
            workers=workers or settings.WORKERS,
            reload=reload or settings.RELOAD,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True,
        )

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


@cli.command()
@click.option("--revision", default=None, help="迁移版本")
def migrate(revision):
    """运行数据库迁移"""
    try:
        alembic_cfg = setup_alembic()
        if revision:
            command.upgrade(alembic_cfg, revision)
        else:
            command.upgrade(alembic_cfg, "head")
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("name")
def makemigrations(name):
    """创建新的迁移"""
    try:
        alembic_cfg = setup_alembic()
        command.revision(alembic_cfg, autogenerate=True, message=name)
        logger.info(f"Created new migration: {name}")
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        sys.exit(1)


@cli.command()
def shell():
    """启动交互式shell"""
    try:
        import IPython
        from database.db import db_manager
        from main import app

        banner = """
        Master Server Interactive Shell
        
        Available objects:
        - app: FastAPI application instance
        - settings: Application settings
        - db_manager: Database manager instance
        """

        IPython.embed(banner1=banner)
    except ImportError:
        logger.error(
            "IPython is required for shell. Install it with: pip install ipython"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start shell: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
