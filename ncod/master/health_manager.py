import os
import psutil
from typing import Dict, List, Optional
from datetime import datetime
from .models import Slave, Device, db
from .utils.redis_cache import cache
from .utils.logger import get_logger

logger = get_logger(__name__)


class HealthManager:
    _instance: Optional['HealthManager'] = None
    
    def __new__(cls) -> 'HealthManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {}
    
    def get_database_status(self) -> Dict:
        """获取数据库状态"""
        try:
            # 检查数据库连接
            db.session.execute('SELECT 1')
            db_status = True
            error_msg = None
            
        except Exception as e:
            db_status = False
            error_msg = str(e)
            
        try:
            # 获取表记录数
            slave_count = Slave.query.count()
            device_count = Device.query.count()
            
            return {
                'status': db_status,
                'error': error_msg,
                'tables': {
                    'slave': slave_count,
                    'device': device_count
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get database status: {e}")
            return {
                'status': False,
                'error': str(e),
                'tables': {},
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_redis_status(self) -> Dict:
        """获取Redis状态"""
        try:
            # 检查Redis连接
            cache.exists('health_check')
            redis_status = True
            error_msg = None
            
            # 获取Redis信息
            info = cache._redis.info()
            
            return {
                'status': redis_status,
                'error': error_msg,
                'info': {
                    'used_memory': info['used_memory'],
                    'used_memory_peak': info['used_memory_peak'],
                    'connected_clients': info['connected_clients'],
                    'uptime_in_seconds': info['uptime_in_seconds']
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get Redis status: {e}")
            return {
                'status': False,
                'error': str(e),
                'info': {},
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_slave_health(self) -> List[Dict]:
        """获取从服务器健康状态"""
        try:
            slaves = []
            current_time = datetime.utcnow()
            
            for slave in Slave.query.all():
                # 检查心跳时间
                if slave.last_heartbeat:
                    time_diff = (
                        current_time - slave.last_heartbeat
                    ).total_seconds()
                    is_alive = time_diff < 300  # 5分钟内有心跳
                else:
                    is_alive = False
                    time_diff = None
                
                # 获取设备数量
                device_count = Device.query.filter_by(
                    slave_id=slave.id
                ).count()
                
                slaves.append({
                    'id': slave.id,
                    'hostname': slave.hostname,
                    'ip_address': slave.ip_address,
                    'status': slave.status,
                    'is_alive': is_alive,
                    'last_heartbeat_seconds': time_diff,
                    'device_count': device_count
                })
                
            return slaves
            
        except Exception as e:
            logger.error(f"Failed to get slave health: {e}")
            return []
    
    def get_device_health(self) -> Dict:
        """获取设备健康状态"""
        try:
            total = Device.query.count()
            online = Device.query.filter_by(status='online').count()
            offline = Device.query.filter_by(status='offline').count()
            in_use = Device.query.filter_by(status='in_use').count()
            
            return {
                'total': total,
                'status': {
                    'online': online,
                    'offline': offline,
                    'in_use': in_use
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get device health: {e}")
            return {
                'total': 0,
                'status': {
                    'online': 0,
                    'offline': 0,
                    'in_use': 0
                },
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def check_log_files(self) -> Dict:
        """检查日志文件状态"""
        try:
            log_dir = 'logs'
            log_files = []
            total_size = 0
            
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    if filename.endswith('.log'):
                        file_path = os.path.join(log_dir, filename)
                        file_stat = os.stat(file_path)
                        
                        log_files.append({
                            'name': filename,
                            'size': file_stat.st_size,
                            'modified': datetime.fromtimestamp(
                                file_stat.st_mtime
                            ).isoformat()
                        })
                        
                        total_size += file_stat.st_size
                        
            return {
                'files': log_files,
                'total_size': total_size,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to check log files: {e}")
            return {
                'files': [],
                'total_size': 0,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_full_health_report(self) -> Dict:
        """获取完整健康报告"""
        return {
            'system': self.get_system_status(),
            'database': self.get_database_status(),
            'redis': self.get_redis_status(),
            'slaves': self.get_slave_health(),
            'devices': self.get_device_health(),
            'logs': self.check_log_files(),
            'timestamp': datetime.utcnow().isoformat()
        } 