import logging
from datetime import datetime, timedelta
from typing import Dict
from ..models import Device, Slave, db
from ..utils.redis_cache import cache

class DeviceMonitor:
    def __init__(self):
        self.logger = logging.getLogger('DeviceMonitor')
        
    @cache.memoize(timeout=30)
    def get_device_status(self) -> Dict:
        try:
            devices = Device.query.all()
            slaves = Slave.query.all()
            
            status = {
                'devices': {
                    'total': len(devices),
                    'online': 0,
                    'offline': 0,
                    'in_use': 0
                },
                'slaves': {
                    'total': len(slaves),
                    'online': 0,
                    'offline': 0
                }
            }
            
            offline_threshold = datetime.utcnow() - timedelta(seconds=90)
            
            for device in devices:
                if device.status == 'in_use':
                    status['devices']['in_use'] += 1
                if device.last_seen > offline_threshold:
                    status['devices']['online'] += 1
                else:
                    status['devices']['offline'] += 1
                    
            for slave in slaves:
                if slave.last_heartbeat > offline_threshold:
                    status['slaves']['online'] += 1
                else:
                    status['slaves']['offline'] += 1
                    
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting device status: {e}")
            return {}
            
    def check_offline_devices(self):
        try:
            offline_threshold = datetime.utcnow() - timedelta(seconds=90)
            offline_devices = Device.query.filter(
                Device.last_seen < offline_threshold,
                Device.status != 'offline'
            ).all()
            
            for device in offline_devices:
                device.status = 'offline'
                self.logger.warning(
                    f"Device {device.vendor_id}:{device.product_id} marked as offline"
                )
                
            db.session.commit()
            cache.delete('device_status')
            
        except Exception as e:
            self.logger.error(f"Error checking offline devices: {e}")
            
    def check_slave_status(self):
        try:
            offline_threshold = datetime.utcnow() - timedelta(seconds=90)
            offline_slaves = Slave.query.filter(
                Slave.last_heartbeat < offline_threshold,
                Slave.status != 'offline'
            ).all()
            
            for slave in offline_slaves:
                slave.status = 'offline'
                self.logger.warning(f"Slave {slave.hostname} marked as offline")
                
                # 将从服务器上的所有设备标记为离线
                Device.query.filter_by(slave_id=slave.id).update(
                    {"status": "offline"}
                )
                
            db.session.commit()
            cache.delete('device_status')
            cache.delete('slave_status')
            
        except Exception as e:
            self.logger.error(f"Error checking slave status: {e}") 