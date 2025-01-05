from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from sqlalchemy.sql import desc
from .models import db, Device, DeviceNotification
from .utils.logger import get_logger
from .config_manager import ConfigManager

logger = get_logger(__name__)
config = ConfigManager()


class DeviceNotifier:
    _instance: Optional['DeviceNotifier'] = None
    
    def __new__(cls) -> 'DeviceNotifier':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def send_alert_notification(
        self,
        alert: Any,
        channels: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """发送告警通知"""
        try:
            # 获取通知配置
            notification_config = config.get_notification_config()
            if not notification_config:
                logger.error("Notification configuration not found")
                return None
                
            # 确定通知渠道
            if not channels:
                channels = notification_config.get(
                    'default_channels',
                    ['email']
                )
                
            # 创建通知记录
            notification = DeviceNotification(
                device_id=alert.device_id,
                notification_type='alert',
                message=alert.message,
                severity=alert.severity,
                channels=channels,
                status='pending',
                metadata={
                    'alert_id': alert.id,
                    'alert_type': alert.alert_type,
                    'device_name': alert.device.name
                },
                created_at=datetime.now()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # 发送通知
            self._send_notification(notification)
            
            logger.info(
                f"Alert notification sent: {alert.device.name} -> {channels}"
            )
            return cast(Dict[str, Any], notification.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")
            db.session.rollback()
            return None
    
    def send_alert_resolution_notification(
        self,
        alert: Any,
        channels: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """发送告警解决通知"""
        try:
            # 获取通知配置
            notification_config = config.get_notification_config()
            if not notification_config:
                logger.error("Notification configuration not found")
                return None
                
            # 确定通知渠道
            if not channels:
                channels = notification_config.get(
                    'default_channels',
                    ['email']
                )
                
            # 创建通知记录
            notification = DeviceNotification(
                device_id=alert.device_id,
                notification_type='alert_resolution',
                message=f"Alert resolved: {alert.message}",
                severity='info',
                channels=channels,
                status='pending',
                metadata={
                    'alert_id': alert.id,
                    'alert_type': alert.alert_type,
                    'device_name': alert.device.name,
                    'resolution': alert.resolution
                },
                created_at=datetime.now()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # 发送通知
            self._send_notification(notification)
            
            logger.info(
                f"Alert resolution notification sent: {alert.device.name}"
            )
            return cast(Dict[str, Any], notification.to_dict())
            
        except Exception as e:
            logger.error(
                f"Failed to send alert resolution notification: {e}"
            )
            db.session.rollback()
            return None
    
    def _send_notification(self, notification: Any) -> None:
        """发送通知"""
        try:
            for channel in notification.channels:
                if channel == 'email':
                    self._send_email_notification(notification)
                elif channel == 'sms':
                    self._send_sms_notification(notification)
                elif channel == 'webhook':
                    self._send_webhook_notification(notification)
                else:
                    logger.warning(
                        f"Unsupported notification channel: {channel}"
                    )
                    
            notification.status = 'sent'
            notification.sent_at = datetime.now()
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            notification.status = 'failed'
            notification.error_message = str(e)
            db.session.commit()
    
    def _send_email_notification(self, notification: Any) -> None:
        """发送邮件通知"""
        try:
            # TODO: 实现邮件发送逻辑
            pass
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            raise
    
    def _send_sms_notification(self, notification: Any) -> None:
        """发送短信通知"""
        try:
            # TODO: 实现短信发送逻辑
            pass
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")
            raise
    
    def _send_webhook_notification(self, notification: Any) -> None:
        """发送Webhook通知"""
        try:
            # TODO: 实现Webhook发送逻辑
            pass
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            raise
    
    def get_notifications(
        self,
        device_id: Optional[int] = None,
        notification_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取通知记录"""
        try:
            query = DeviceNotification.query
            
            if device_id:
                query = query.filter_by(device_id=device_id)
            if notification_type:
                query = query.filter_by(notification_type=notification_type)
            if severity:
                query = query.filter_by(severity=severity)
            if status:
                query = query.filter_by(status=status)
            if start_date:
                query = query.filter(
                    DeviceNotification.created_at >= start_date
                )
            if end_date:
                query = query.filter(
                    DeviceNotification.created_at <= end_date
                )
                
            notifications = query.order_by(
                desc(DeviceNotification.created_at)
            ).offset(offset).limit(limit).all()
            
            return [
                cast(Dict[str, Any], notif.to_dict())
                for notif in notifications
            ]
            
        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
            return []
    
    def get_notification_summary(
        self,
        device_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取通知摘要"""
        try:
            query = DeviceNotification.query
            
            if device_id:
                query = query.filter_by(device_id=device_id)
            if start_date:
                query = query.filter(
                    DeviceNotification.created_at >= start_date
                )
            if end_date:
                query = query.filter(
                    DeviceNotification.created_at <= end_date
                )
                
            # 总通知数
            total_notifications = query.count()
            
            # 按类型统计
            type_counts: Dict[str, int] = {}
            for notif_type in query.with_entities(
                DeviceNotification.notification_type
            ).distinct().all():
                count = query.filter_by(
                    notification_type=notif_type[0]
                ).count()
                type_counts[notif_type[0]] = count
                
            # 按严重程度统计
            severity_counts: Dict[str, int] = {}
            for severity in ['info', 'warning', 'error', 'critical']:
                count = query.filter_by(severity=severity).count()
                severity_counts[severity] = count
                
            # 按状态统计
            status_counts: Dict[str, int] = {}
            for status in ['pending', 'sent', 'failed']:
                count = query.filter_by(status=status).count()
                status_counts[status] = count
                
            # 按渠道统计
            channel_counts: Dict[str, int] = {}
            for notification in query.all():
                for channel in notification.channels:
                    channel_counts[channel] = (
                        channel_counts.get(channel, 0) + 1
                    )
                    
            return {
                'total_notifications': total_notifications,
                'type_counts': type_counts,
                'severity_counts': severity_counts,
                'status_counts': status_counts,
                'channel_counts': channel_counts
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification summary: {e}")
            return {
                'total_notifications': 0,
                'type_counts': {},
                'severity_counts': {},
                'status_counts': {},
                'channel_counts': {}
            } 