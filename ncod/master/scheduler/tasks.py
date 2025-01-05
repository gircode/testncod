"""任务调度器模块"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ncod.core.logger import master_logger as logger
from ncod.core.config import config
from ncod.master.services.monitor import MonitorService
from ncod.master.services.device import DeviceService


class TaskScheduler:
    def __init__(self):
        self.running = False
        self.monitor_service = MonitorService()
        self.device_service = DeviceService()
        self.tasks: Dict[str, asyncio.Task] = {}

    async def start(self):
        """启动任务调度器"""
        self.running = True
        # 启动定时任务
        self.tasks["cleanup"] = asyncio.create_task(self._cleanup_task())
        self.tasks["metrics"] = asyncio.create_task(self._metrics_task())
        self.tasks["device_check"] = asyncio.create_task(self._device_check_task())
        logger.info("Task scheduler started")

    async def stop(self):
        """停止任务调度器"""
        self.running = False
        # 取消所有任务
        for task in self.tasks.values():
            task.cancel()
        # 等待任务完成
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.tasks.clear()
        logger.info("Task scheduler stopped")

    async def _cleanup_task(self):
        """清理任务"""
        cleanup_interval = config.scheduler.get("cleanup_interval", 3600)  # 默认1小时
        while self.running:
            try:
                # 清理过期的监控数据
                await self.monitor_service.cleanup_old_metrics()
                # 清理过期的设备使用记录
                await self.device_service.cleanup_usage_logs()
                logger.info("Cleanup task completed")
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(cleanup_interval)

    async def _metrics_task(self):
        """指标收集任务"""
        metrics_interval = config.scheduler.get("metrics_interval", 60)  # 默认1分钟
        while self.running:
            try:
                # 收集系统指标
                await self.monitor_service.collect_system_metrics()
                # 检查告警条件
                await self.monitor_service.check_alerts()
                logger.info("Metrics collection completed")
            except Exception as e:
                logger.error(f"Error in metrics task: {e}")
            await asyncio.sleep(metrics_interval)

    async def _device_check_task(self):
        """设备检查任务"""
        check_interval = config.scheduler.get("device_check_interval", 300)  # 默认5分钟
        while self.running:
            try:
                # 检查设备状态
                await self.device_service.check_devices_status()
                # 更新设备统计信息
                await self.device_service.update_device_statistics()
                logger.info("Device check completed")
            except Exception as e:
                logger.error(f"Error in device check task: {e}")
            await asyncio.sleep(check_interval)

    def add_task(self, name: str, coro, interval: int):
        """添加自定义任务"""

        async def _task_wrapper():
            while self.running:
                try:
                    await coro()
                except Exception as e:
                    logger.error(f"Error in task {name}: {e}")
                await asyncio.sleep(interval)

        self.tasks[name] = asyncio.create_task(_task_wrapper())
        logger.info(f"Added task: {name}")

    def remove_task(self, name: str):
        """移除任务"""
        if name in self.tasks:
            self.tasks[name].cancel()
            del self.tasks[name]
            logger.info(f"Removed task: {name}")
