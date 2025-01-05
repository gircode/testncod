import asyncio
from typing import Dict, List
import aiohttp
from ncod.master.core.config import settings
from ncod.master.core.logger import logger
from ncod.master.models.slave import Slave


class SlaveDiscovery:
    """从服务器发现服务"""

    def __init__(self):
        self.discovery_port = settings.DISCOVERY_PORT
        self._running = False
        self._known_slaves = {}

    async def start(self):
        """启动发现服务"""
        if self._running:
            return
        self._running = True
        logger.info("Starting slave discovery service")
        asyncio.create_task(self._discovery_loop())

    async def stop(self):
        """停止发现服务"""
        if not self._running:
            return
        self._running = False
        logger.info("Stopping slave discovery service")

    async def _discovery_loop(self):
        """发现服务主循环"""
        while self._running:
            try:
                await self._scan_network()
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}")
            await asyncio.sleep(30)  # 每30秒扫描一次

    async def _scan_network(self):
        """扫描网络寻找从服务器"""
        async with aiohttp.ClientSession() as session:
            for ip in self._generate_ip_range():
                try:
                    url = f"http://{ip}:{self.discovery_port}/api/slave/info"
                    async with session.get(url, timeout=2) as response:
                        if response.status == 200:
                            slave_info = await response.json()
                            await self._register_slave(slave_info)
                except Exception as e:
                    continue

    def _generate_ip_range(self) -> List[str]:
        """生成要扫描的IP地址范围"""
        # 这里应该根据实际网络环境配置IP范围
        return ["192.168.1." + str(i) for i in range(1, 255)]

    async def _register_slave(self, slave_info: Dict):
        """注册新发现的从服务器"""
        slave_id = slave_info.get("id")
        if slave_id not in self._known_slaves:
            self._known_slaves[slave_id] = slave_info
            logger.info(f"New slave discovered: {slave_id}")
            await self._notify_master(slave_info)

    async def _notify_master(self, slave_info: Dict):
        """通知主服务器有新的从服务器加入"""
        try:
            master_url = f"http://localhost:{settings.MASTER_PORT}/api/slaves/register"
            async with aiohttp.ClientSession() as session:
                async with session.post(master_url, json=slave_info) as response:
                    if response.status == 200:
                        logger.info(
                            f"Successfully registered slave {slave_info.get('id')}"
                        )
                    else:
                        logger.error(f"Failed to register slave {slave_info.get('id')}")
        except Exception as e:
            logger.error(f"Error notifying master: {e}")

    async def get_slave_info(self, slave_id: str) -> Dict:
        """获取从服务器信息"""
        return self._known_slaves.get(slave_id, {})
