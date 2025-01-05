"""从服务器发现客户端"""

import asyncio
import json
import socket
from typing import Optional, Dict
from datetime import datetime
from ncod.core.logger import setup_logger
from ncod.core.config import config

logger = setup_logger("discovery_client")


class DiscoveryClient:
    """发现客户端"""

    def __init__(self):
        self.node_id = str(config.slave_id)
        self.master_url = config.master_url
        self.registered = False
        self.running = False

    async def register(self) -> bool:
        """注册到主服务器"""
        try:
            info = {
                "hostname": socket.gethostname(),
                "ip": socket.gethostbyname(socket.gethostname()),
                "port": config.slave_port,
                "capabilities": self.get_capabilities(),
                "registered_at": datetime.utcnow().isoformat(),
            }

            # 发送注册请求
            async with self.session.post(
                f"{self.master_url}/api/v1/discovery/register",
                json={"node_id": self.node_id, "info": info},
            ) as response:
                if response.status == 200:
                    self.registered = True
                    logger.info("Successfully registered with master")
                    return True
                else:
                    logger.error(f"Registration failed: {await response.text()}")
                    return False
        except Exception as e:
            logger.error(f"Error registering with master: {e}")
            return False

    async def unregister(self) -> bool:
        """从主服务器注销"""
        try:
            async with self.session.post(
                f"{self.master_url}/api/v1/discovery/unregister",
                json={"node_id": self.node_id},
            ) as response:
                if response.status == 200:
                    self.registered = False
                    logger.info("Successfully unregistered from master")
                    return True
                else:
                    logger.error(f"Unregistration failed: {await response.text()}")
                    return False
        except Exception as e:
            logger.error(f"Error unregistering from master: {e}")
            return False

    def get_capabilities(self) -> Dict:
        """获取节点能力"""
        return {
            "max_devices": config.max_devices,
            "supported_types": config.supported_device_types,
            "features": config.supported_features,
        }

    async def start(self):
        """启动客户端"""
        self.running = True
        while self.running:
            try:
                if not self.registered:
                    if await self.register():
                        break
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in discovery client: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        """停止客户端"""
        self.running = False
        if self.registered:
            await self.unregister()
