"""
设备统计信息管理模块

此模块提供设备性能、同步和告警统计信息的管理功能，包括：
- 设备性能统计（CPU、内存、磁盘等）
- 设备同步统计（成功率、重试次数等）
- 设备告警统计（告警数量、解决率等）
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from .models import db, Device, DeviceStatus, DeviceAlert, DeviceSync
from .utils.logger import get_logger
from .config_manager import ConfigManager

logger = get_logger(__name__)
config = ConfigManager()


class DeviceStatsManager:
    """设备统计信息管理器，负责收集和更新设备相关的统计数据"""

    _instance: Optional['DeviceStatsManager'] = None

    def __new__(cls) -> 'DeviceStatsManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def update_device_stats(self, device_id: int) -> bool:
        """更新设备统计信息"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error("Device not found: %d", device_id)
                return False

            # 计算统计时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)

            # 获取状态记录
            status_records = DeviceStatus.query.filter_by(
                device_id=device_id
            ).filter(
                DeviceStatus.created_at >= start_time,
                DeviceStatus.created_at <= end_time
            ).all()

            # 计算性能指标
            total_records = len(status_records)
            if total_records > 0:
                cpu_usage = sum(
                    record.cpu_usage for record in status_records
                ) / total_records
                memory_usage = sum(
                    record.memory_usage for record in status_records
                ) / total_records
                disk_usage = sum(
                    record.disk_usage for record in status_records
                ) / total_records
                network_usage = sum(
                    record.network_usage for record in status_records
                ) / total_records
                temperature = sum(
                    record.temperature for record in status_records
                ) / total_records
            else:
                cpu_usage = 0.0
                memory_usage = 0.0
                disk_usage = 0.0
                network_usage = 0.0
                temperature = 0.0

            # 计算在线率
            online_records = sum(
                1 for record in status_records
                if record.status == 'online'
            )
            uptime = (
                online_records / total_records * 100
                if total_records > 0 else 0
            )

            # 更新设备统计信息
            device.stats = {
                'avg_cpu_usage': round(cpu_usage, 2),
                'avg_memory_usage': round(memory_usage, 2),
                'avg_disk_usage': round(disk_usage, 2),
                'avg_network_usage': round(network_usage, 2),
                'avg_temperature': round(temperature, 2),
                'uptime_percentage': round(uptime, 2),
                'total_records': total_records,
                'updated_at': end_time.isoformat()
            }

            db.session.commit()

            logger.info("Device stats updated: %s", device.name)
            return True

        except (ValueError, AttributeError) as e:
            logger.error("Failed to update device stats: %s", str(e))
            db.session.rollback()
            return False

    def update_sync_stats(self, device_id: int) -> bool:
        """更新同步统计信息"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error("Device not found: %d", device_id)
                return False

            # 计算统计时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)

            # 获取同步记录
            sync_records = DeviceSync.query.filter_by(
                device_id=device_id
            ).filter(
                DeviceSync.created_at >= start_time,
                DeviceSync.created_at <= end_time
            ).all()

            # 计算同步统计
            total_syncs = len(sync_records)
            if total_syncs > 0:
                successful_syncs = sum(
                    1 for record in sync_records
                    if record.status == 'completed'
                )
                failed_syncs = sum(
                    1 for record in sync_records
                    if record.status == 'failed'
                )
                total_retries = sum(
                    record.retry_count for record in sync_records
                )
                avg_retries = total_retries / total_syncs
            else:
                successful_syncs = 0
                failed_syncs = 0
                avg_retries = 0

            # 更新设备同步统计信息
            if not device.stats:
                device.stats = {}

            device.stats.update({
                'total_syncs': total_syncs,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'avg_retries': round(avg_retries, 2),
                'sync_success_rate': round(
                    successful_syncs / total_syncs * 100
                    if total_syncs > 0 else 0,
                    2
                ),
                'sync_stats_updated_at': end_time.isoformat()
            })

            db.session.commit()

            logger.info("Device sync stats updated: %s", device.name)
            return True

        except (ValueError, AttributeError) as e:
            logger.error("Failed to update sync stats: %s", str(e))
            db.session.rollback()
            return False

    def update_alert_stats(self, device_id: int) -> bool:
        """更新告警统计信息"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error("Device not found: %d", device_id)
                return False

            # 计算统计时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)

            # 获取告警记录
            alert_records = DeviceAlert.query.filter_by(
                device_id=device_id
            ).filter(
                DeviceAlert.created_at >= start_time,
                DeviceAlert.created_at <= end_time
            ).all()

            # 计算告警统计
            total_alerts = len(alert_records)
            if total_alerts > 0:
                active_alerts = sum(
                    1 for record in alert_records
                    if record.status == 'active'
                )
                resolved_alerts = sum(
                    1 for record in alert_records
                    if record.status == 'resolved'
                )
                critical_alerts = sum(
                    1 for record in alert_records
                    if record.severity == 'critical'
                )
                # 计算平均解决时间
                resolution_times = [
                    (alert.resolved_at - alert.created_at).total_seconds()
                    for alert in alert_records
                    if alert.status == 'resolved' and alert.resolved_at
                ]
                avg_resolution_time = (
                    sum(resolution_times) / len(resolution_times)
                    if resolution_times else 0
                )
            else:
                active_alerts = 0
                resolved_alerts = 0
                critical_alerts = 0
                avg_resolution_time = 0

            # 更新设备告警统计信息
            if not device.stats:
                device.stats = {}

            device.stats.update({
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'resolved_alerts': resolved_alerts,
                'critical_alerts': critical_alerts,
                'avg_resolution_time': round(avg_resolution_time, 2),
                'alert_resolution_rate': round(
                    resolved_alerts / total_alerts * 100
                    if total_alerts > 0 else 0,
                    2
                ),
                'alert_stats_updated_at': end_time.isoformat()
            })

            db.session.commit()

            logger.info("Device alert stats updated: %s", device.name)
            return True

        except (ValueError, AttributeError) as e:
            logger.error("Failed to update alert stats: %s", str(e))
            db.session.rollback()
            return False

    def get_device_stats(
        self,
        device_id: int,
        include_history: bool = False
    ) -> Optional[Dict[str, Any]]:
        """获取设备统计信息"""
        try:
            device = Device.query.get(device_id)
            if not device:
                logger.error("Device not found: %d", device_id)
                return None

            return device.stats

        except (ValueError, AttributeError) as e:
            logger.error("Failed to get device stats: %s", str(e))
            return None 