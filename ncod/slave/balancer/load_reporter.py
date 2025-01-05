"""负载报告客户端"""

import asyncio
import json
import psutil
import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger("load_reporter")


class LoadReporter:
    """负载报告器"""

    def __init__(self, node_id: str, master_host: str, master_port: int = 5679):
        self.node_id = node_id
        self.master_host = master_host
        self.master_port = master_port
        self.running = False

    async def start(self):
        """启动报告器"""
        try:
            self.running = True
            logger.info("Load reporter started")
            asyncio.create_task(self._report_load())
        except Exception as e:
            logger.error(f"Error starting load reporter: {e}")
            self.running = False
            raise

    async def stop(self):
        """停止报告器"""
        try:
            self.running = False
            logger.info("Load reporter stopped")
        except Exception as e:
            logger.error(f"Error stopping load reporter: {e}")
            raise

    def _get_system_load(self) -> Dict:
        """获取系统负载"""
        try:
            return {
                "cpu": psutil.cpu_percent(),
                "memory": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage("/").percent,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting system load: {e}")
            return {}

    async def _report_load(self):
        """报告负载"""
        while self.running:
            try:
                # 获取系统负载
                load_info = self._get_system_load()
                if not load_info:
                    continue

                # 发送负载信息
                reader, writer = await asyncio.open_connection(
                    self.master_host, self.master_port
                )

                message = {"node_id": self.node_id, "load": load_info}

                writer.write(json.dumps(message).encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()

            except Exception as e:
                logger.error(f"Error reporting load: {e}")

            await asyncio.sleep(5)
