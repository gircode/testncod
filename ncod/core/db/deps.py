"""数据库依赖"""

import logging
from typing import AsyncGenerator, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from ncod.core.db.pool import DatabasePool
from ncod.core.db.transaction import TransactionManager
from ncod.core.db.optimizer import QueryOptimizer
from ncod.core.db.monitor import DatabaseMonitor

logger = logging.getLogger("db_deps")

# 创建数据库连接池实例
db_pool = DatabasePool()

# 创建事务管理器实例
transaction_manager = TransactionManager(db_pool)

# 创建查询优化器实例
query_optimizer = QueryOptimizer(db_pool)

# 创建数据库监控器实例
db_monitor = DatabaseMonitor(db_pool)


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """获取读取数据库会话"""
    session = db_pool.get_read_session()
    try:
        yield session
    finally:
        await session.close()


async def get_write_db() -> AsyncGenerator[AsyncSession, None]:
    """获取写入数据库会话"""
    session = db_pool.get_write_session()
    try:
        yield session
    finally:
        await session.close()


async def get_transaction() -> AsyncGenerator[TransactionManager, None]:
    """获取事务管理器"""
    yield transaction_manager


async def get_optimizer() -> AsyncGenerator[QueryOptimizer, None]:
    """获取查询优化器"""
    yield query_optimizer


async def get_monitor() -> AsyncGenerator[DatabaseMonitor, None]:
    """获取数据库监控器"""
    yield db_monitor


# 依赖注入函数类型
ReadDB = Callable[[], AsyncGenerator[AsyncSession, None]]
WriteDB = Callable[[], AsyncGenerator[AsyncSession, None]]
Transaction = Callable[[], AsyncGenerator[TransactionManager, None]]
Optimizer = Callable[[], AsyncGenerator[QueryOptimizer, None]]
Monitor = Callable[[], AsyncGenerator[DatabaseMonitor, None]]

# 创建依赖实例
get_read_session = get_read_db
get_write_session = get_write_db
get_transaction_manager = get_transaction
get_query_optimizer = get_optimizer
get_db_monitor = get_monitor
