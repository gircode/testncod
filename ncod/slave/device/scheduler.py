"""设备调度器"""

import asyncio
from typing import Dict, List, Optional, Tuple, NamedTuple
from datetime import datetime, timedelta
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.slave.device.manager import device_manager

logger = setup_logger("device_scheduler")


class QueueEntry(NamedTuple):
    """队列条目"""

    user_id: str
    priority: int


class DeviceScheduler:
    """设备调度器"""

    def __init__(self):
        self.manager = device_manager
        self.running = False
        self.device_queue: Dict[str, List[QueueEntry]] = {}
        self.max_wait_time = config.max_device_wait_time
        self.max_use_time = config.max_device_use_time

    async def start(self):
        """启动调度器"""
        try:
            self.running = True
            asyncio.create_task(self._scheduling_loop())
            logger.info("Device scheduler started")
        except Exception as e:
            logger.error(f"Error starting device scheduler: {e}")
            raise

    async def stop(self):
        """停止调度器"""
        try:
            self.running = False
            logger.info("Device scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping device scheduler: {e}")

    async def request_device(
        self, device_id: str, user_id: str, priority: int = 0
    ) -> Tuple[bool, str]:
        """请求设备使用"""
        try:
            device_info = self.manager.controller.get_device_info(device_id)
            if not device_info:
                return False, "Device not found"

            if device_info["status"] == "available":
                success = await self.manager.request_device(device_id, user_id)
                if success:
                    return True, "Device assigned"
                return False, "Failed to assign device"

            if device_id not in self.device_queue:
                self.device_queue[device_id] = []

            queue = self.device_queue[device_id]
            insert_pos = len(queue)
            for i, entry in enumerate(queue):
                if priority > entry.priority:
                    insert_pos = i
                    break

            queue.insert(insert_pos, QueueEntry(user_id, priority))
            return True, "Added to queue"
        except Exception as e:
            logger.error(f"Error requesting device: {e}")
            return False, str(e)

    async def release_device(self, device_id: str, user_id: str) -> Tuple[bool, str]:
        """释放设备"""
        try:
            success = await self.manager.release_device(device_id, user_id)
            if success:
                # 检查等待队列
                await self._process_device_queue(device_id)
            return success, "Device released"
        except Exception as e:
            logger.error(f"Error releasing device: {e}")
            return False, str(e)

    async def _scheduling_loop(self):
        """调度循环"""
        while self.running:
            try:
                await self._check_timeouts()
                await self._process_all_queues()
                await asyncio.sleep(config.scheduling_interval)
            except Exception as e:
                logger.error(f"Error in scheduling loop: {e}")
                await asyncio.sleep(5)

    async def _check_timeouts(self):
        """检查超时"""
        try:
            current_time = datetime.utcnow()
            for device_id, device in self.manager.controller.devices.items():
                if device["status"] != "in_use":
                    continue

                usage = self.manager.device_usage.get(device_id, {})
                current_session = usage.get("current_session")
                if not current_session:
                    continue

                # 检查使用时间是否超过限制
                start_time = current_session["start_time"]
                if (current_time - start_time) > timedelta(seconds=self.max_use_time):
                    user_id = current_session["user_id"]
                    await self.release_device(device_id, user_id)
                    logger.info(f"Released device {device_id} due to timeout")
        except Exception as e:
            logger.error(f"Error checking timeouts: {e}")

    async def _process_device_queue(self, device_id: str):
        """处理设备队列"""
        try:
            if device_id not in self.device_queue:
                return

            queue = self.device_queue[device_id]
            if not queue:
                return

            device_info = self.manager.controller.get_device_info(device_id)
            if not device_info or device_info["status"] != "available":
                return

            entry = queue.pop(0)
            success = await self.manager.request_device(device_id, entry.user_id)
            if success:
                logger.info(
                    f"Assigned device {device_id} to queued user {entry.user_id}"
                )
            else:
                queue.append(QueueEntry(entry.user_id, 0))
        except Exception as e:
            logger.error(f"Error processing device queue: {e}")

    async def _process_all_queues(self):
        """处理所有队列"""
        try:
            for device_id in list(self.device_queue.keys()):
                await self._process_device_queue(device_id)
        except Exception as e:
            logger.error(f"Error processing all queues: {e}")

    def get_queue_position(self, device_id: str, user_id: str) -> Optional[int]:
        """获取用户在队列中的位置"""
        try:
            queue = self.device_queue.get(device_id, [])
            for i, (queued_user, _) in enumerate(queue):
                if queued_user == user_id:
                    return i
            return None
        except Exception as e:
            logger.error(f"Error getting queue position: {e}")
            return None


# 创建全局设备调度器实例
device_scheduler = DeviceScheduler()
