"""设备监控模块"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Set
import aiohttp
from prometheus_client import Counter, Gauge, Histogram

from ncod.utils.logger import logger
from ncod.utils.config import settings
from ncod.utils.cache import redis_cache
from ncod.models.device import Device, DeviceStatus

# Prometheus指标
DEVICE_CONNECT_TOTAL = Counter(
    "device_connect_total", "设备连接总次数", ["device_id", "status"]
)

DEVICE_CONNECT_DURATION = Histogram(
    "device_connect_duration_seconds", "设备连接持续时间", ["device_id"]
)

DEVICE_STATUS = Gauge("device_status", "设备状态", ["device_id", "status"])


class DeviceMonitor:
    """设备监控器"""

    def __init__(self):
        self._running = False
        self._monitored_devices: Dict[str, DeviceStatus] = {}
        self._connection_times: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def start(self):
        """启动监控"""
        if self._running:
            return

        self._running = True
        logger.info("启动设备监控")
        asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """停止监控"""
        if not self._running:
            return

        self._running = False
        logger.info("停止设备监控")

    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                await self._check_devices()
                await self._update_metrics()
                await self._check_timeouts()
            except Exception as e:
                logger.error(f"设备监控错误: {e}")
            await asyncio.sleep(5)  # 每5秒检查一次

    async def _check_devices(self):
        """检查设备状态"""
        async with aiohttp.ClientSession() as session:
            for device_id, status in self._monitored_devices.items():
                try:
                    # 检查设备连接状态
                    device_url = f"http://{settings.VH_SERVER_HOST}:{settings.VH_SERVER_PORT}/device/{device_id}"
                    async with session.get(device_url) as response:
                        if response.status == 200:
                            device_info = await response.json()
                            await self._update_device_status(device_id, device_info)
                        else:
                            await self._handle_device_offline(device_id)
                except Exception as e:
                    logger.error(f"检查设备 {device_id} 状态失败: {e}")
                    await self._handle_device_offline(device_id)

    async def _update_device_status(self, device_id: str, device_info: Dict):
        """更新设备状态"""
        async with self._lock:
            old_status = self._monitored_devices.get(device_id)
            new_status = DeviceStatus(**device_info)

            if old_status != new_status:
                self._monitored_devices[device_id] = new_status
                await self._handle_status_change(device_id, old_status, new_status)

    async def _handle_status_change(
        self,
        device_id: str,
        old_status: Optional[DeviceStatus],
        new_status: DeviceStatus,
    ):
        """处理状态变化"""
        # 更新Prometheus指标
        DEVICE_STATUS.labels(device_id=device_id, status=new_status.status).set(1)

        if old_status:
            DEVICE_STATUS.labels(device_id=device_id, status=old_status.status).set(0)

        # 记录连接事件
        if new_status.status == "connected":
            if device_id not in self._connection_times:
                self._connection_times[device_id] = datetime.utcnow()
                DEVICE_CONNECT_TOTAL.labels(device_id=device_id, status="success").inc()

        elif old_status and old_status.status == "connected":
            if device_id in self._connection_times:
                start_time = self._connection_times.pop(device_id)
                duration = (datetime.utcnow() - start_time).total_seconds()
                DEVICE_CONNECT_DURATION.labels(device_id=device_id).observe(duration)

        # 发送通知
        await self._notify_status_change(device_id, new_status)

    async def _handle_device_offline(self, device_id: str):
        """处理设备离线"""
        async with self._lock:
            if device_id in self._monitored_devices:
                old_status = self._monitored_devices[device_id]
                if old_status.status != "offline":
                    new_status = DeviceStatus(
                        id=device_id, status="offline", last_seen=datetime.utcnow()
                    )
                    await self._handle_status_change(device_id, old_status, new_status)
                    self._monitored_devices[device_id] = new_status

    async def _update_metrics(self):
        """更新监控指标"""
        # 更新设备总数
        total_devices = len(self._monitored_devices)
        connected_devices = sum(
            1
            for status in self._monitored_devices.values()
            if status.status == "connected"
        )

        # 更新Prometheus指标
        DEVICE_STATUS.labels(device_id="total", status="total").set(total_devices)

        DEVICE_STATUS.labels(device_id="total", status="connected").set(
            connected_devices
        )

    async def _check_timeouts(self):
        """检查超时设备"""
        now = datetime.utcnow()
        timeout = settings.DEVICE_TIMEOUT  # 设备超时时间(秒)

        async with self._lock:
            for device_id, status in self._monitored_devices.items():
                if (
                    status.status != "offline"
                    and (now - status.last_seen).total_seconds() > timeout
                ):
                    await self._handle_device_offline(device_id)

    async def _notify_status_change(self, device_id: str, status: DeviceStatus):
        """发送状态变化通知"""
        try:
            # 获取设备信息
            device = await Device.get_by_id(device_id)
            if not device:
                return

            # 构建通知消息
            message = {
                "type": "device_status",
                "device_id": device_id,
                "device_name": device.name,
                "status": status.status,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # 发送到Redis通知队列
            await redis_cache.publish("device_notifications", message)

        except Exception as e:
            logger.error(f"发送设备状态通知失败: {e}")

    async def add_device(self, device_id: str):
        """添加监控设备"""
        async with self._lock:
            if device_id not in self._monitored_devices:
                self._monitored_devices[device_id] = DeviceStatus(
                    id=device_id, status="unknown", last_seen=datetime.utcnow()
                )
                logger.info(f"添加设备监控: {device_id}")

    async def remove_device(self, device_id: str):
        """移除监控设备"""
        async with self._lock:
            if device_id in self._monitored_devices:
                del self._monitored_devices[device_id]
                if device_id in self._connection_times:
                    del self._connection_times[device_id]
                logger.info(f"移除设备监控: {device_id}")

    def get_device_status(self, device_id: str) -> Optional[DeviceStatus]:
        """获取设备状态"""
        return self._monitored_devices.get(device_id)

    def get_all_statuses(self) -> Dict[str, DeviceStatus]:
        """获取所有设备状态"""
        return self._monitored_devices.copy()


# 创建全局监控器实例
device_monitor = DeviceMonitor()
