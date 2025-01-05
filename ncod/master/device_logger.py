from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from sqlalchemy.sql import desc
from .models import db, Device, DeviceLog
from .utils.logger import get_logger
from .config_manager import ConfigManager

logger = get_logger(__name__)
config = ConfigManager()


class DeviceLogManager:
    _instance: Optional['DeviceLogManager'] = None
    
    def __new__(cls) -> 'DeviceLogManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def log_event(
        self,
        device_id: int,
        event_type: str,
        message: str,
        severity: str = 'info',
        source: str = 'system',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """记录设备事件"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return None
                
            # 创建日志记录
            log_entry = DeviceLog(
                device_id=device_id,
                event_type=event_type,
                message=message,
                severity=severity,
                source=source,
                metadata=metadata or {},
                created_at=datetime.now()
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
            logger.info(
                f"Event logged: {device.name} - {event_type} - {severity}"
            )
            return cast(Dict[str, Any], log_entry.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            db.session.rollback()
            return None
    
    def get_device_logs(
        self,
        device_id: Optional[int] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        source: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取设备日志"""
        try:
            query = DeviceLog.query
            
            if device_id:
                query = query.filter_by(device_id=device_id)
            if event_type:
                query = query.filter_by(event_type=event_type)
            if severity:
                query = query.filter_by(severity=severity)
            if source:
                query = query.filter_by(source=source)
            if start_date:
                query = query.filter(DeviceLog.created_at >= start_date)
            if end_date:
                query = query.filter(DeviceLog.created_at <= end_date)
                
            logs = query.order_by(
                desc(DeviceLog.created_at)
            ).offset(offset).limit(limit).all()
            
            return [
                cast(Dict[str, Any], log.to_dict()) for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Failed to get device logs: {e}")
            return []
    
    def get_log_summary(
        self,
        device_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取日志摘要"""
        try:
            query = DeviceLog.query
            
            if device_id:
                query = query.filter_by(device_id=device_id)
            if start_date:
                query = query.filter(DeviceLog.created_at >= start_date)
            if end_date:
                query = query.filter(DeviceLog.created_at <= end_date)
                
            # 总日志数
            total_logs = query.count()
            
            # 按事件类型统计
            type_counts: Dict[str, int] = {}
            for event_type in query.with_entities(
                DeviceLog.event_type
            ).distinct().all():
                count = query.filter_by(event_type=event_type[0]).count()
                type_counts[event_type[0]] = count
                
            # 按严重程度统计
            severity_counts: Dict[str, int] = {}
            for severity in ['debug', 'info', 'warning', 'error', 'critical']:
                count = query.filter_by(severity=severity).count()
                severity_counts[severity] = count
                
            # 按来源统计
            source_counts: Dict[str, int] = {}
            for source in query.with_entities(
                DeviceLog.source
            ).distinct().all():
                count = query.filter_by(source=source[0]).count()
                source_counts[source[0]] = count
                
            # 按设备统计
            device_counts: Dict[int, int] = {}
            for device_id in query.with_entities(
                DeviceLog.device_id
            ).distinct().all():
                count = query.filter_by(device_id=device_id[0]).count()
                device_counts[device_id[0]] = count
                
            # 计算平均每小时日志数
            if start_date and end_date:
                hours = (end_date - start_date).total_seconds() / 3600
                logs_per_hour = total_logs / hours if hours > 0 else 0
            else:
                logs_per_hour = 0
                
            return {
                'total_logs': total_logs,
                'type_counts': type_counts,
                'severity_counts': severity_counts,
                'source_counts': source_counts,
                'device_counts': device_counts,
                'logs_per_hour': logs_per_hour
            }
            
        except Exception as e:
            logger.error(f"Failed to get log summary: {e}")
            return {
                'total_logs': 0,
                'type_counts': {},
                'severity_counts': {},
                'source_counts': {},
                'device_counts': {},
                'logs_per_hour': 0
            }
    
    def clear_old_logs(
        self,
        days: int = 30,
        device_id: Optional[int] = None
    ) -> bool:
        """清理旧日志"""
        try:
            cutoff_date = datetime.now() - datetime.timedelta(days=days)
            query = DeviceLog.query.filter(
                DeviceLog.created_at < cutoff_date
            )
            
            if device_id:
                query = query.filter_by(device_id=device_id)
                
            deleted_count = query.delete()
            db.session.commit()
            
            logger.info(f"Cleared {deleted_count} old logs")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear old logs: {e}")
            db.session.rollback()
            return False
    
    def export_logs(
        self,
        device_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = 'json'
    ) -> Optional[str]:
        """导出日志"""
        try:
            logs = self.get_device_logs(
                device_id=device_id,
                start_date=start_date,
                end_date=end_date,
                limit=10000  # 限制导出数量
            )
            
            if not logs:
                logger.error("No logs to export")
                return None
                
            if format == 'json':
                import json
                return json.dumps(logs, default=str)
            elif format == 'csv':
                import csv
                import io
                output = io.StringIO()
                writer = csv.DictWriter(
                    output,
                    fieldnames=logs[0].keys()
                )
                writer.writeheader()
                writer.writerows(logs)
                return output.getvalue()
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return None 