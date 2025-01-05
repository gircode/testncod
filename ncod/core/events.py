"""应用事件处理"""

from typing import Callable
from fastapi import FastAPI
from sqlalchemy.engine import Engine
from sqlalchemy import event

from .db.base import Base
from .db.database import engine
from ..utils.logger import logger


def init_db(app: FastAPI) -> None:
    """初始化数据库"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error("数据库初始化失败", exc_info=True)
        raise


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """设置SQLite配置"""
    if "sqlite" in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_start_app_handler(app: FastAPI) -> Callable:
    """创建应用启动处理程序"""

    async def start_app() -> None:
        init_db(app)

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    """创建应用停止处理程序"""

    async def stop_app() -> None:
        try:
            await engine.dispose()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error("关闭数据库连接失败", exc_info=True)

    return stop_app
