"""数据库监控器"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload
from ncod.core.db.pool import DatabasePool
from ncod.core.logger import setup_logger

logger = setup_logger("db_monitor")


class DatabaseMonitor:
    """数据库监控器"""

    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self.running = False

    async def start(self):
        """启动监控器"""
        try:
            self.running = True
            logger.info("Database monitor started")
        except Exception as e:
            logger.error(f"Error starting database monitor: {e}")
            self.running = False
            raise

    async def stop(self):
        """停止监控器"""
        try:
            self.running = False
            logger.info("Database monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping database monitor: {e}")
            raise

    async def get_pool_metrics(self) -> Dict:
        """获取连接池指标"""
        try:
            return await self.db_pool.get_pool_status()
        except Exception as e:
            logger.error(f"Error getting pool metrics: {e}")
            return {}

    async def get_query_metrics(self) -> Dict:
        """获取查询性能指标"""
        try:
            write_pool = self.db_pool.write_engine.pool
            return {
                "active_sessions": write_pool.checkedout(),
                "idle_sessions": write_pool.checkedin(),
                "total_sessions": write_pool.size(),
                "overflow": write_pool.overflow(),
            }
        except Exception as e:
            logger.error(f"Error getting query metrics: {e}")
            return {}

    async def check_pool_health(self) -> bool:
        """检查连接池健康状态"""
        try:
            metrics = await self.get_pool_metrics()
            write_pool = metrics.get("write_pool", {})

            # 检查连接池使用率
            if write_pool.get("overflow", 0) > 5:
                logger.warning("High connection pool overflow")
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking pool health: {e}")
            return False
