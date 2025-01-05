"""从服务器心跳客户端"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

# 创建日志记录器
logger = logging.getLogger("heartbeat_client")
logger.setLevel(logging.INFO)


class HeartbeatClient:
    """心跳客户端"""

    def __init__(self, node_id: str, interval: int = 5):
        self.node_id = node_id
        self.interval = interval
        self.running = False
        self.last_sent: Optional[datetime] = None

    async def start(self):
        """启动心跳"""
        try:
            self.running = True
            logger.info("Heartbeat client started")
            asyncio.create_task(self._send_heartbeat())
        except Exception as e:
            logger.error(f"Error starting heartbeat client: {e}")
            self.running = False
            raise

    async def stop(self):
        """停止心跳"""
        try:
            self.running = False
            logger.info("Heartbeat client stopped")
        except Exception as e:
            logger.error(f"Error stopping heartbeat client: {e}")
            raise

    async def _send_heartbeat(self):
        """发送心跳"""
        while self.running:
            try:
                # 这里添加实际的心跳发送逻辑
                self.last_sent = datetime.utcnow()
                logger.debug(f"Sent heartbeat at {self.last_sent}")
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
                await asyncio.sleep(1)

    def get_last_sent(self) -> Optional[datetime]:
        """获取最后发送时间"""
        return self.last_sent
