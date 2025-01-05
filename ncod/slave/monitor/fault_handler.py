"""故障处理器"""

import asyncio
from typing import Dict, List, Optional, Callable, Awaitable, Any
from datetime import datetime
from dataclasses import dataclass
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.slave.monitor.alert import alert_system
from ncod.slave.device.manager import device_manager
from ncod.slave.monitor.collector import metrics_collector

logger = setup_logger("fault_handler")


@dataclass
class FaultRule:
    """故障规则"""

    name: str
    description: str
    check_func: Callable[[], bool]
    recovery_func: Callable[[], Awaitable[None]]
    severity: str  # critical, major, minor
    auto_recover: bool


class FaultHandler:
    """故障处理器"""

    def __init__(self):
        self.running = False
        self.rules: List[FaultRule] = []
        self.active_faults: Dict[str, datetime] = {}
        self.recovery_attempts: Dict[str, int] = {}
        self.max_recovery_attempts = config.max_recovery_attempts
        self._init_rules()

    def _init_rules(self):
        """初始化故障规则"""
        self.rules = [
            FaultRule(
                name="device_connection_lost",
                description="设备连接丢失",
                check_func=self._check_device_connection,
                recovery_func=self._recover_device_connection,
                severity="major",
                auto_recover=True,
            ),
            FaultRule(
                name="high_resource_usage",
                description="系统资源使用过高",
                check_func=self._check_resource_usage,
                recovery_func=self._recover_resource_usage,
                severity="critical",
                auto_recover=True,
            ),
            FaultRule(
                name="device_error_state",
                description="设备错误状态",
                check_func=self._check_device_errors,
                recovery_func=self._recover_device_errors,
                severity="major",
                auto_recover=True,
            ),
        ]

    async def start(self):
        """启动故障处理器"""
        try:
            self.running = True
            asyncio.create_task(self._fault_check_loop())
            logger.info("Fault handler started")
        except Exception as e:
            logger.error(f"Error starting fault handler: {e}")
            raise

    async def stop(self):
        """停止故障处理器"""
        try:
            self.running = False
            logger.info("Fault handler stopped")
        except Exception as e:
            logger.error(f"Error stopping fault handler: {e}")

    def _check_device_connection(self) -> bool:
        """检查设备连接状态"""
        try:
            devices = device_manager.controller.devices
            for device_id, device in devices.items():
                if device["status"] == "error" or device["status"] == "disconnected":
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking device connection: {e}")
            return False

    async def _recover_device_connection(self):
        """恢复设备连接"""
        try:
            devices = device_manager.controller.devices
            for device_id, device in devices.items():
                if device["status"] == "error" or device["status"] == "disconnected":
                    # 尝试重新连接设备
                    await device_manager.controller.reconnect_device(device_id)
        except Exception as e:
            logger.error(f"Error recovering device connection: {e}")

    def _check_resource_usage(self) -> bool:
        """检查资源使用情况"""
        try:
            metrics = metrics_collector.get_current_metrics()
            system_metrics = metrics.get("system", {})
            return (
                system_metrics.get("cpu_usage", 0) > 90
                or system_metrics.get("memory_usage", 0) > 90
            )
        except Exception as e:
            logger.error(f"Error checking resource usage: {e}")
            return False

    async def _recover_resource_usage(self):
        """恢复资源使用"""
        try:
            # 释放一些资源
            await self._release_inactive_devices()
            # 可以添加其他资源释放策略
        except Exception as e:
            logger.error(f"Error recovering resource usage: {e}")

    async def _release_inactive_devices(self):
        """释放不活跃设备"""
        try:
            devices = device_manager.controller.devices
            for device_id, device in devices.items():
                if device["status"] == "in_use":
                    usage = device_manager.get_device_usage(device_id)
                    if usage and usage.get("idle_time", 0) > config.max_idle_time:
                        await device_manager.release_device(
                            device_id, usage["current_session"]["user_id"]
                        )
        except Exception as e:
            logger.error(f"Error releasing inactive devices: {e}")

    def _check_device_errors(self) -> bool:
        """检查设备错误"""
        try:
            devices = device_manager.controller.devices
            return any(device["status"] == "error" for device in devices.values())
        except Exception as e:
            logger.error(f"Error checking device errors: {e}")
            return False

    async def _recover_device_errors(self):
        """恢复设备错误"""
        try:
            devices = device_manager.controller.devices
            for device_id, device in devices.items():
                if device["status"] == "error":
                    await device_manager.controller.reset_device(device_id)
        except Exception as e:
            logger.error(f"Error recovering device errors: {e}")

    async def _fault_check_loop(self):
        """故障检查循环"""
        while self.running:
            try:
                await self._check_and_recover_faults()
                await asyncio.sleep(config.fault_check_interval)
            except Exception as e:
                logger.error(f"Error in fault check loop: {e}")
                await asyncio.sleep(5)

    async def _check_and_recover_faults(self):
        """检查并恢复故障"""
        try:
            for rule in self.rules:
                if rule.check_func():
                    if rule.name not in self.active_faults:
                        # 新故障
                        self.active_faults[rule.name] = datetime.utcnow()
                        self.recovery_attempts[rule.name] = 0
                        logger.error(
                            f"Fault detected: {rule.name} - {rule.description}"
                        )

                    if rule.auto_recover:
                        attempts = self.recovery_attempts.get(rule.name, 0)
                        if attempts < self.max_recovery_attempts:
                            await rule.recovery_func()
                            self.recovery_attempts[rule.name] = attempts + 1
                            logger.info(
                                f"Recovery attempt {attempts + 1} "
                                f"for fault: {rule.name}"
                            )
                else:
                    # 故障已解决
                    if rule.name in self.active_faults:
                        del self.active_faults[rule.name]
                        del self.recovery_attempts[rule.name]
                        logger.info(f"Fault resolved: {rule.name}")
        except Exception as e:
            logger.error(f"Error checking and recovering faults: {e}")

    def get_active_faults(self) -> Dict[str, datetime]:
        """获取活动故障"""
        return self.active_faults.copy()


# 创建全局故障处理器实例
fault_handler = FaultHandler()
