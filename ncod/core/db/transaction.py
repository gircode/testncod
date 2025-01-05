"""事务管理器"""

import logging
from typing import Optional, Callable, TypeVar, Any, AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from ncod.core.db.pool import DatabasePool
from ncod.core.logger import setup_logger

logger = setup_logger("transaction")

T = TypeVar("T")


class TransactionManager:
    """事务管理器"""

    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        """事务上下文管理器"""
        session = self.db_pool.get_write_session()
        try:
            async with session.begin():
                yield session
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

    async def run_in_transaction(
        self, func: Callable[[AsyncSession, ...], T], *args: Any, **kwargs: Any
    ) -> T:
        """在事务中运行函数"""
        async with self.transaction() as session:
            try:
                result = await func(session, *args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Error running in transaction: {e}")
                raise

    @asynccontextmanager
    async def distributed_transaction(
        self, participants: list[AsyncSession]
    ) -> AsyncIterator[list[AsyncSession]]:
        """分布式事务上下文管理器"""
        try:
            # 准备阶段
            for session in participants:
                await session.begin()

            yield participants

            # 提交阶段
            success = True
            for session in participants:
                try:
                    await session.commit()
                except Exception as e:
                    logger.error(f"Error committing transaction: {e}")
                    success = False
                    break

            # 如果有任何提交失败，回滚所有事务
            if not success:
                for session in participants:
                    try:
                        await session.rollback()
                    except Exception as e:
                        logger.error(f"Error rolling back transaction: {e}")

        except Exception as e:
            logger.error(f"Distributed transaction error: {e}")
            # 回滚所有事务
            for session in participants:
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error rolling back transaction: {rollback_error}")
            raise
        finally:
            # 关闭所有会话
            for session in participants:
                await session.close()
