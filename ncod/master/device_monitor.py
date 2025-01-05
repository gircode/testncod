from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from sqlalchemy.sql import desc
from .models import db, Device, DeviceStatus
from .utils.logger import get_logger
from .config_manager import ConfigManager
from .device_alert import DeviceAlertManager
from .device_stats import DeviceStatsManager

logger = get_logger(__name__)
config = ConfigManager()
alert_manager = DeviceAlertManager()
stats_manager = DeviceStatsManager()


class DeviceMonitorManager:
    _instance: Optional['DeviceMonitorManager'] = None
    
    def __new__(cls) -> 'DeviceMonitorManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def update_device_status(
        self,
        device_id: int,
        status: str,
        metrics: Dict[str, float],
        message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """更新设备状态"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return None
                
            # 创建状态记录
            status_record = DeviceStatus(
                device_id=device_id,
                status=status,
                cpu_usage=metrics.get('cpu_usage', 0.0),
                memory_usage=metrics.get('memory_usage', 0.0),
                disk_usage=metrics.get('disk_usage', 0.0),
                network_usage=metrics.get('network_usage', 0.0),
                temperature=metrics.get('temperature', 0.0),
                message=message or '',
                created_at=datetime.now()
            )
            
            db.session.add(status_record)
            
            # 更新设备当前状态
            device.status = status
            device.status_message = message or ''
            device.updated_at = datetime.now()
            
            db.session.commit()
            
            # 检查是否需要触发告警
            self._check_alerts(device_id, metrics)
            
            # 更新设备统计信息
            stats_manager.update_device_stats(device_id)
            
            logger.info(f"Device status updated: {device.name} -> {status}")
            return cast(Dict[str, Any], status_record.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to update device status: {e}")
            db.session.rollback()
            return None
    
    def _check_alerts(
        self,
        device_id: int,
        metrics: Dict[str, float]
    ) -> None:
        """检查是否需要触发告警"""
        try:
            # 获取设备告警阈值配置
            thresholds = config.get_device_thresholds(device_id)
            if not thresholds:
                return
                
            # 检查CPU使用率
            cpu_usage = metrics.get('cpu_usage', 0.0)
            if cpu_usage > thresholds.get('cpu_threshold', 90.0):
                alert_manager.create_alert(
                    device_id=device_id,
                    alert_type='high_cpu_usage',
                    message=f'CPU usage is {cpu_usage}%',
                    severity='warning'
                )
                
            # 检查内存使用率
            memory_usage = metrics.get('memory_usage', 0.0)
            if memory_usage > thresholds.get('memory_threshold', 90.0):
                alert_manager.create_alert(
                    device_id=device_id,
                    alert_type='high_memory_usage',
                    message=f'Memory usage is {memory_usage}%',
                    severity='warning'
                )
                
            # 检查磁盘使用率
            disk_usage = metrics.get('disk_usage', 0.0)
            if disk_usage > thresholds.get('disk_threshold', 90.0):
                alert_manager.create_alert(
                    device_id=device_id,
                    alert_type='high_disk_usage',
                    message=f'Disk usage is {disk_usage}%',
                    severity='warning'
                )
                
            # 检查温度
            temperature = metrics.get('temperature', 0.0)
            if temperature > thresholds.get('temperature_threshold', 80.0):
                alert_manager.create_alert(
                    device_id=device_id,
                    alert_type='high_temperature',
                    message=f'Temperature is {temperature}°C',
                    severity='warning'
                )
                
        except Exception as e:
            logger.error(f"Failed to check alerts: {e}")
    
    def get_device_status(
        self,
        device_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取设备状态历史"""
        try:
            query = DeviceStatus.query.filter_by(device_id=device_id)
            
            if start_date:
                query = query.filter(DeviceStatus.created_at >= start_date)
            if end_date:
                query = query.filter(DeviceStatus.created_at <= end_date)
                
            status_records = query.order_by(
                desc(DeviceStatus.created_at)
            ).offset(offset).limit(limit).all()
            
            return [
                cast(Dict[str, Any], record.to_dict())
                for record in status_records
            ]
            
        except Exception as e:
            logger.error(f"Failed to get device status: {e}")
            return []
    
    def get_status_summary(
        self,
        device_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取状态摘要"""
        try:
            query = DeviceStatus.query
            
            if device_id:
                query = query.filter_by(device_id=device_id)
            if start_date:
                query = query.filter(DeviceStatus.created_at >= start_date)
            if end_date:
                query = query.filter(DeviceStatus.created_at <= end_date)
                
            # 计算平均值
            metrics = db.session.query(
                db.func.avg(DeviceStatus.cpu_usage).label('avg_cpu'),
                db.func.avg(DeviceStatus.memory_usage).label('avg_memory'),
                db.func.avg(DeviceStatus.disk_usage).label('avg_disk'),
                db.func.avg(DeviceStatus.network_usage).label('avg_network'),
                db.func.avg(DeviceStatus.temperature).label('avg_temp')
            ).first()
            
            # 计算最大值
            max_metrics = db.session.query(
                db.func.max(DeviceStatus.cpu_usage).label('max_cpu'),
                db.func.max(DeviceStatus.memory_usage).label('max_memory'),
                db.func.max(DeviceStatus.disk_usage).label('max_disk'),
                db.func.max(DeviceStatus.network_usage).label('max_network'),
                db.func.max(DeviceStatus.temperature).label('max_temp')
            ).first()
            
            # 按状态统计
            status_counts: Dict[str, int] = {}
            for status in ['online', 'offline', 'error', 'maintenance']:
                count = query.filter_by(status=status).count()
                status_counts[status] = count
                
            # 计算设备在线率
            total_records = query.count()
            online_records = query.filter_by(status='online').count()
            uptime = (
                online_records / total_records * 100
                if total_records > 0 else 0
            )
            
            return {
                'status_counts': status_counts,
                'uptime_percentage': uptime,
                'averages': {
                    'cpu_usage': float(metrics.avg_cpu or 0),
                    'memory_usage': float(metrics.avg_memory or 0),
                    'disk_usage': float(metrics.avg_disk or 0),
                    'network_usage': float(metrics.avg_network or 0),
                    'temperature': float(metrics.avg_temp or 0)
                },
                'maximums': {
                    'cpu_usage': float(max_metrics.max_cpu or 0),
                    'memory_usage': float(max_metrics.max_memory or 0),
                    'disk_usage': float(max_metrics.max_disk or 0),
                    'network_usage': float(max_metrics.max_network or 0),
                    'temperature': float(max_metrics.max_temp or 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get status summary: {e}")
            return {
                'status_counts': {},
                'uptime_percentage': 0,
                'averages': {
                    'cpu_usage': 0,
                    'memory_usage': 0,
                    'disk_usage': 0,
                    'network_usage': 0,
                    'temperature': 0
                },
                'maximums': {
                    'cpu_usage': 0,
                    'memory_usage': 0,
                    'disk_usage': 0,
                    'network_usage': 0,
                    'temperature': 0
                }
            } 