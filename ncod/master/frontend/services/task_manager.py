"""Task Manager模块"""

import asyncio
import datetime
import json
import logging
from typing import Any, Dict, List

from database import db_manager
from models.user import Alert, Device, DeviceBackup, SecurityScan, Task
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self):
        self.running = False
        self.task_handlers = {
            "backup": self.handle_backup_task,
            "update": self.handle_update_task,
            "security_scan": self.handle_security_scan_task,
            "monitoring": self.handle_monitoring_task,
        }

    async def start(self):
        """启动任务管理器"""
        self.running = True
        while self.running:
            try:
                await self.process_pending_tasks()
                await self.schedule_automated_tasks()
                await asyncio.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"Task manager error: {e}")

    async def stop(self):
        """停止任务管理器"""
        self.running = False

    async def process_pending_tasks(self):
        """处理待执行的任务"""
        try:
            with db_manager.get_session() as session:
                pending_tasks = (
                    session.query(Task)
                    .filter(Task.status == "pending")
                    .order_by(Task.created_at.asc())
                    .all()
                )

                for task in pending_tasks:
                    handler = self.task_handlers.get(task.type)
                    if handler:
                        task.status = "running"
                        session.commit()

                        try:
                            await handler(task)
                            task.status = "completed"
                        except Exception as e:
                            task.status = "failed"
                            task.result = {"error": str(e)}
                            logger.error(f"Task {task.id} failed: {e}")

                        task.updated_at = datetime.datetime.utcnow()
                        session.commit()

        except Exception as e:
            logger.error(f"Error processing pending tasks: {e}")

    async def schedule_automated_tasks(self):
        """调度自动化任务"""
        try:
            with db_manager.get_session() as session:
                # 检查需要备份的设备
                devices_need_backup = (
                    session.query(Device)
                    .filter(
                        and_(
                            Device.backup_config.isnot(None),
                            Device.last_backup
                            < datetime.datetime.utcnow() - datetime.timedelta(hours=24),
                        )
                    )
                    .all()
                )

                for device in devices_need_backup:
                    await self.create_backup_task(device)

                # 检查需要安全扫描的设备
                devices_need_scan = (
                    session.query(Device)
                    .filter(
                        and_(
                            Device.security_config.isnot(None),
                            Device.last_security_scan
                            < datetime.datetime.utcnow() - datetime.timedelta(days=7),
                        )
                    )
                    .all()
                )

                for device in devices_need_scan:
                    await self.create_security_scan_task(device)

        except Exception as e:
            logger.error(f"Error scheduling automated tasks: {e}")

    async def handle_backup_task(self, task: Task):
        """处理备份任务"""
        try:
            with db_manager.get_session() as session:
                device = session.query(Device).get(task.device_id)
                if not device:
                    raise Exception("Device not found")

                # 创建备份记录
                backup = DeviceBackup(
                    device_id=device.id,
                    type=task.result.get("backup_type", "config"),
                    status="running",
                    created_at=datetime.datetime.utcnow(),
                    expires_at=datetime.datetime.utcnow()
                    + datetime.timedelta(days=task.result.get("retention_days", 30)),
                )
                session.add(backup)
                session.commit()

                # 执行备份操作（根据设备类型使用不同的备份方法）
                if device.type == "network":
                    await self._backup_network_device(device, backup)
                elif device.type == "storage":
                    await self._backup_storage_device(device, backup)
                elif device.type in ["virtualization", "container"]:
                    await self._backup_virtual_platform(device, backup)
                else:
                    await self._backup_server(device, backup)

                device.last_backup = datetime.datetime.utcnow()
                session.commit()

        except Exception as e:
            logger.error(f"Backup task failed: {e}")
            raise

    async def handle_update_task(self, task: Task):
        """处理更新任务"""
        try:
            with db_manager.get_session() as session:
                device = session.query(Device).get(task.device_id)
                if not device:
                    raise Exception("Device not found")

                # 执行更新操作（根据设备类型使用不同的更新方法）
                if device.type == "network":
                    await self._update_network_device(device, task.result)
                elif device.type == "storage":
                    await self._update_storage_device(device, task.result)
                elif device.type in ["virtualization", "container"]:
                    await self._update_virtual_platform(device, task.result)
                else:
                    await self._update_server(device, task.result)

        except Exception as e:
            logger.error(f"Update task failed: {e}")
            raise

    async def handle_security_scan_task(self, task: Task):
        """处理安全扫描任务"""
        try:
            with db_manager.get_session() as session:
                device = session.query(Device).get(task.device_id)
                if not device:
                    raise Exception("Device not found")

                # 创建扫描记录
                scan = SecurityScan(
                    device_id=device.id,
                    scan_type=task.result.get("scan_type", "vulnerability"),
                    status="running",
                    created_at=datetime.datetime.utcnow(),
                )
                session.add(scan)
                session.commit()

                # 执行安全扫描（根据设备类型使用不同的扫描方法）
                findings = []
                if device.type == "network":
                    findings = await self._scan_network_device(device)
                elif device.type == "storage":
                    findings = await self._scan_storage_device(device)
                elif device.type in ["virtualization", "container"]:
                    findings = await self._scan_virtual_platform(device)
                else:
                    findings = await self._scan_server(device)

                # 更新扫描结果
                scan.findings = findings
                scan.risk_level = self._calculate_risk_level(findings)
                scan.status = "completed"
                scan.completed_at = datetime.datetime.utcnow()

                # 创建告警
                if findings:
                    alert = Alert(
                        device_id=device.id,
                        alert_type="security",
                        severity=scan.risk_level,
                        title=f"Security scan found {len(findings)} issues",
                        message=json.dumps(findings[:3]),  # 只显示前3个问题
                        created_at=datetime.datetime.utcnow(),
                    )
                    session.add(alert)

                device.last_security_scan = datetime.datetime.utcnow()
                session.commit()

        except Exception as e:
            logger.error(f"Security scan task failed: {e}")
            raise

    async def handle_monitoring_task(self, task: Task):
        """处理监控任务"""
        try:
            with db_manager.get_session() as session:
                device = session.query(Device).get(task.device_id)
                if not device:
                    raise Exception("Device not found")

                # 获取监控数据
                metrics = await self._collect_device_metrics(device)

                # 检查告警阈值
                for metric in metrics:
                    if self._check_alert_threshold(device, metric):
                        alert = Alert(
                            device_id=device.id,
                            alert_type="monitoring",
                            severity=metric["severity"],
                            title=f"{metric['name']} exceeded threshold",
                            message=f"Current value: {metric['value']} \
                                 {metric['unit']}",
                            created_at=datetime.datetime.utcnow(),
                        )
                        session.add(alert)

                session.commit()

        except Exception as e:
            logger.error(f"Monitoring task failed: {e}")
            raise

    def _calculate_risk_level(self, findings: List[Dict[str, Any]]) -> str:
        """计算风险等级"""
        if not findings:
            return "low"

        severity_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        max_severity = max(
            findings, key=lambda x: severity_scores.get(x.get("severity", "low"), 0)
        ).get("severity", "low")

        return max_severity

    def _check_alert_threshold(self, device: Device, metric: Dict[str, Any]) -> bool:
        """检查是否超过告警阈值"""
        thresholds = device.monitoring_config.get("thresholds", {})
        if metric["name"] not in thresholds:
            return False

        threshold = thresholds[metric["name"]]
        value = float(metric["value"])

        if threshold["operator"] == ">":
            return value > threshold["value"]
        elif threshold["operator"] == "<":
            return value < threshold["value"]
        elif threshold["operator"] == ">=":
            return value >= threshold["value"]
        elif threshold["operator"] == "<=":
            return value <= threshold["value"]

        return False

    # 以下是设备特定的操作方法，需要根据实际设备类型实现
    async def _backup_network_device(self, device: Device, backup: DeviceBackup):
        """备份网络设备配置"""
        pass

    async def _backup_storage_device(self, device: Device, backup: DeviceBackup):
        """备份存储设备"""
        pass

    async def _backup_virtual_platform(self, device: Device, backup: DeviceBackup):
        """备份虚拟化平台"""
        pass

    async def _backup_server(self, device: Device, backup: DeviceBackup):
        """备份服务器"""
        pass

    async def _update_network_device(self, device: Device, params: Dict[str, Any]):
        """更新网络设备"""
        pass

    async def _update_storage_device(self, device: Device, params: Dict[str, Any]):
        """更新存储设备"""
        pass

    async def _update_virtual_platform(self, device: Device, params: Dict[str, Any]):
        """更新虚拟化平台"""
        pass

    async def _update_server(self, device: Device, params: Dict[str, Any]):
        """更新服务器"""
        pass

    async def _scan_network_device(self, device: Device) -> List[Dict[str, Any]]:
        """扫描网络设备"""
        return []

    async def _scan_storage_device(self, device: Device) -> List[Dict[str, Any]]:
        """扫描存储设备"""
        return []

    async def _scan_virtual_platform(self, device: Device) -> List[Dict[str, Any]]:
        """扫描虚拟化平台"""
        return []

    async def _scan_server(self, device: Device) -> List[Dict[str, Any]]:
        """扫描服务器"""
        return []

    async def _collect_device_metrics(self, device: Device) -> List[Dict[str, Any]]:
        """收集设备指标"""
        return []


# 创建全局任务管理器实例
task_manager = TaskManager()
