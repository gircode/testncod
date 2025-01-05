"""通知服务"""

from typing import Dict, Any
import aiohttp
from ncod.master.config import settings


class NotifyService:
    @staticmethod
    async def send_notification(channel: str, config: Dict[str, Any], message: str):
        if channel == "webhook":
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config["url"], json={"message": message}
                ) as response:
                    return await response.json()
        # ... 其他通知渠道的实现
