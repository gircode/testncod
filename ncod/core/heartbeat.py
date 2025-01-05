"""心跳检测模块"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

# 创建日志记录器
logger = logging.getLogger("heartbeat")
logger.setLevel(logging.INFO)


class HeartbeatMonitor:
    """心跳监控器"""

    def __init__(self, interval: int = 5):
        self.interval = interval
        self.last_beats: Dict[str, datetime] = {}
        self.running = False

    async def start(self):
        """启动监控"""
        try:
            self.running = True
            logger.info("Heartbeat monitor started")
            asyncio.create_task(self._check_heartbeats())
        except Exception as e:
            logger.error(f"Error starting heartbeat monitor: {e}")
            self.running = False
            raise

    async def stop(self):
        """停止监控"""
        try:
            self.running = False
            logger.info("Heartbeat monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping heartbeat monitor: {e}")
            raise

    async def _check_heartbeats(self):
        """检查心跳"""
        while self.running:
            try:
                now = datetime.utcnow()
                for node_id, last_beat in self.last_beats.items():
                    if (now - last_beat).total_seconds() > self.interval * 3:
                        logger.warning(f"Node {node_id} heartbeat timeout")
            except Exception as e:
                logger.error(f"Error checking heartbeats: {e}")
            await asyncio.sleep(self.interval)

    def update_heartbeat(self, node_id: str):
        """更新心跳"""
        try:
            self.last_beats[node_id] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error updating heartbeat for {node_id}: {e}")

    def get_last_heartbeat(self, node_id: str) -> Optional[datetime]:
        """获取最后心跳时间"""
        return self.last_beats.get(node_id)

    def is_node_alive(self, node_id: str) -> bool:
        """检查节点是否存活"""
        try:
            last_beat = self.last_beats.get(node_id)
            if not last_beat:
                return False
            return (datetime.utcnow() - last_beat).total_seconds() <= self.interval * 3
        except Exception as e:
            logger.error(f"Error checking node status for {node_id}: {e}")
            return False
