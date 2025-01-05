from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from sqlalchemy.sql import desc
from .models import db, Device, DeviceAlert
from .utils.logger import get_logger
from .config_manager import ConfigManager
from .device_notifier import DeviceNotifier

logger = get_logger(__name__)
config = ConfigManager()
notifier = DeviceNotifier()


class DeviceAlertManager:
    _instance: Optional['DeviceAlertManager'] = None
    
    def __new__(cls) -> 'DeviceAlertManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_alert(
        self,
        device_id: int,
        alert_type: str,
        message: str,
        severity: str = 'warning',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """创建设备告警"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return None
                
            # 检查是否有相同的未处理告警
            existing = DeviceAlert.query.filter_by(
                device_id=device_id,
                alert_type=alert_type,
                status='active'
            ).first()
            
            if existing:
                # 更新现有告警
                existing.count += 1
                existing.last_occurred_at = datetime.now()
                existing.message = message
                existing.metadata = metadata or {}
                db.session.commit()
                
                logger.info(
                    f"Alert updated: {device.name} -> {alert_type}"
                )
                return cast(Dict[str, Any], existing.to_dict())
                
            # 创建新告警
            alert = DeviceAlert(
                device_id=device_id,
                alert_type=alert_type,
                message=message,
                severity=severity,
                status='active',
                count=1,
                metadata=metadata or {},
                created_at=datetime.now(),
                last_occurred_at=datetime.now()
            )
            
            db.session.add(alert)
            db.session.commit()
            
            # 发送告警通知
            notifier.send_alert_notification(alert)
            
            logger.info(f"Alert created: {device.name} -> {alert_type}")
            return cast(Dict[str, Any], alert.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            db.session.rollback()
            return None
    
    def resolve_alert(
        self,
        alert_id: int,
        resolution: str,
        resolved_by: Optional[int] = None
    ) -> bool:
        """解决告警"""
        try:
            alert = DeviceAlert.query.get(alert_id)
            if not alert:
                logger.error(f"Alert not found: {alert_id}")
                return False
                
            if alert.status != 'active':
                logger.error(
                    f"Alert is not active: {alert_id} -> {alert.status}"
                )
                return False
                
            alert.status = 'resolved'
            alert.resolution = resolution
            alert.resolved_by = resolved_by
            alert.resolved_at = datetime.now()
            
            db.session.commit()
            
            # 发送告警解决通知
            notifier.send_alert_resolution_notification(alert)
            
            logger.info(f"Alert resolved: {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            db.session.rollback()
            return False
    
    def acknowledge_alert(
        self,
        alert_id: int,
        acknowledged_by: Optional[int] = None,
        note: Optional[str] = None
    ) -> bool:
        """确认告警"""
        try:
            alert = DeviceAlert.query.get(alert_id)
            if not alert:
                logger.error(f"Alert not found: {alert_id}")
                return False
                
            if alert.status != 'active':
                logger.error(
                    f"Alert is not active: {alert_id} -> {alert.status}"
                )
                return False
                
            alert.status = 'acknowledged'
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            alert.note = note
            
            db.session.commit()
            
            logger.info(f"Alert acknowledged: {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            db.session.rollback()
            return False
    
    def get_device_alerts(
        self,
        device_id: Optional[int] = None,
        alert_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取设备告警"""
        try:
            query = DeviceAlert.query
            
            if device_id:
                query = query.filter_by(device_id=device_id)
            if alert_type:
                query = query.filter_by(alert_type=alert_type)
            if severity:
                query = query.filter_by(severity=severity)
            if status:
                query = query.filter_by(status=status)
            if start_date:
                query = query.filter(DeviceAlert.created_at >= start_date)
            if end_date:
                query = query.filter(DeviceAlert.created_at <= end_date)
                
            alerts = query.order_by(
                desc(DeviceAlert.created_at)
            ).offset(offset).limit(limit).all()
            
            return [
                cast(Dict[str, Any], alert.to_dict()) for alert in alerts
            ]
            
        except Exception as e:
            logger.error(f"Failed to get device alerts: {e}")
            return []
    
    def get_alert_summary(
        self,
        device_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取告警摘要"""
        try:
            query = DeviceAlert.query
            
            if device_id:
                query = query.filter_by(device_id=device_id)
            if start_date:
                query = query.filter(DeviceAlert.created_at >= start_date)
            if end_date:
                query = query.filter(DeviceAlert.created_at <= end_date)
                
            # 总告警数
            total_alerts = query.count()
            
            # 按类型统计
            type_counts: Dict[str, int] = {}
            for alert_type in query.with_entities(
                DeviceAlert.alert_type
            ).distinct().all():
                count = query.filter_by(alert_type=alert_type[0]).count()
                type_counts[alert_type[0]] = count
                
            # 按严重程度统计
            severity_counts: Dict[str, int] = {}
            for severity in ['info', 'warning', 'error', 'critical']:
                count = query.filter_by(severity=severity).count()
                severity_counts[severity] = count
                
            # 按状态统计
            status_counts: Dict[str, int] = {}
            for status in ['active', 'acknowledged', 'resolved']:
                count = query.filter_by(status=status).count()
                status_counts[status] = count
                
            # 按设备统计
            device_counts: Dict[int, int] = {}
            for device_id in query.with_entities(
                DeviceAlert.device_id
            ).distinct().all():
                count = query.filter_by(device_id=device_id[0]).count()
                device_counts[device_id[0]] = count
                
            # 计算平均解决时间
            resolved_alerts = query.filter_by(status='resolved')
            if resolved_alerts.count() > 0:
                resolution_times = [
                    (alert.resolved_at - alert.created_at).total_seconds()
                    for alert in resolved_alerts.all()
                    if alert.resolved_at
                ]
                avg_resolution_time = (
                    sum(resolution_times) / len(resolution_times)
                    if resolution_times else 0
                )
            else:
                avg_resolution_time = 0
                
            return {
                'total_alerts': total_alerts,
                'type_counts': type_counts,
                'severity_counts': severity_counts,
                'status_counts': status_counts,
                'device_counts': device_counts,
                'avg_resolution_time': avg_resolution_time
            }
            
        except Exception as e:
            logger.error(f"Failed to get alert summary: {e}")
            return {
                'total_alerts': 0,
                'type_counts': {},
                'severity_counts': {},
                'status_counts': {},
                'device_counts': {},
                'avg_resolution_time': 0
            } 