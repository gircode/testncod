"""设备管理器"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.slave.device.controller import device_controller

logger = setup_logger("device_manager")


class DeviceManager:
    """设备管理器"""

    def __init__(self):
        self.controller = device_controller
        self.device_usage: Dict[str, Dict] = {}
        self.running = False

    async def start(self):
        """启动管理器"""
        try:
            self.running = True
            await self.controller.start()
            asyncio.create_task(self._usage_monitor_loop())
            logger.info("Device manager started")
        except Exception as e:
            logger.error(f"Error starting device manager: {e}")
            raise

    async def stop(self):
        """停止管理器"""
        try:
            self.running = False
            await self.controller.stop()
            logger.info("Device manager stopped")
        except Exception as e:
            logger.error(f"Error stopping device manager: {e}")
            raise

    async def _usage_monitor_loop(self):
        """使用情况监控循环"""
        while self.running:
            try:
                await self.update_usage_stats()
                await asyncio.sleep(config.usage_update_interval)
            except Exception as e:
                logger.error(f"Error in usage monitor loop: {e}")
                await asyncio.sleep(5)

    async def update_usage_stats(self):
        """更新使用统计"""
        try:
            devices = self.controller.get_all_devices()
            for device in devices:
                device_id = device["id"]
                if device["status"] == "in_use":
                    if device_id not in self.device_usage:
                        self.device_usage[device_id] = {
                            "total_time": 0,
                            "session_count": 0,
                            "last_connected": None,
                            "current_session": {
                                "start_time": datetime.utcnow(),
                                "user_id": device.get("user_id"),
                            },
                        }
                    # 更新使用时间
                    current_session = self.device_usage[device_id]["current_session"]
                    if current_session:
                        duration = (
                            datetime.utcnow() - current_session["start_time"]
                        ).total_seconds()
                        self.device_usage[device_id]["total_time"] += duration
        except Exception as e:
            logger.error(f"Error updating usage stats: {e}")

    async def request_device(self, device_id: str, user_id: str) -> bool:
        """请求使用设备"""
        try:
            # 检查设备可用性
            device_info = self.controller.get_device_info(device_id)
            if not device_info:
                logger.error(f"Device {device_id} not found")
                return False

            if device_info["status"] != "available":
                logger.error(f"Device {device_id} not available")
                return False

            # 连接设备
            success = await self.controller.connect_device(device_id, user_id)
            if success:
                # 记录使用情况
                if device_id not in self.device_usage:
                    self.device_usage[device_id] = {
                        "total_time": 0,
                        "session_count": 0,
                        "last_connected": None,
                    }

                self.device_usage[device_id].update(
                    {
                        "session_count": self.device_usage[device_id]["session_count"]
                        + 1,
                        "last_connected": datetime.utcnow(),
                        "current_session": {
                            "start_time": datetime.utcnow(),
                            "user_id": user_id,
                        },
                    }
                )

            return success
        except Exception as e:
            logger.error(f"Error requesting device {device_id}: {e}")
            return False

    async def release_device(self, device_id: str, user_id: str) -> bool:
        """释放设备"""
        try:
            # 验证当前用户
            device_usage = self.device_usage.get(device_id, {})
            current_session = device_usage.get("current_session", {})
            if current_session.get("user_id") != user_id:
                logger.error(
                    f"User {user_id} not authorized to release device {device_id}"
                )
                return False

            # 断开设备
            success = await self.controller.disconnect_device(device_id)
            if success:
                # 更新使用记录
                if current_session:
                    duration = (
                        datetime.utcnow() - current_session["start_time"]
                    ).total_seconds()
                    device_usage["total_time"] += duration
                    device_usage["current_session"] = None

            return success
        except Exception as e:
            logger.error(f"Error releasing device {device_id}: {e}")
            return False

    def get_device_usage(self, device_id: str) -> Optional[Dict]:
        """获取设备使用情况"""
        try:
            return self.device_usage.get(device_id)
        except Exception as e:
            logger.error(f"Error getting device usage for {device_id}: {e}")
            return None

    def get_all_usage_stats(self) -> Dict[str, Dict]:
        """获取所有设备使用统计"""
        return self.device_usage.copy()


# 创建全局设备管理器实例
device_manager = DeviceManager()
