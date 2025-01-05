from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from sqlalchemy.sql import desc
from .models import Device, DeviceUsage
from .utils.logger import get_logger
from .config_manager import ConfigManager
from .device_manager import DeviceManager

logger = get_logger(__name__)
config = ConfigManager()
device_manager = DeviceManager()


class DeviceScheduler:
    _instance: Optional['DeviceScheduler'] = None
    
    def __new__(cls) -> 'DeviceScheduler':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def schedule_device(
        self,
        device_type: str,
        user_id: int,
        duration: Optional[int] = None,
        slave_id: Optional[int] = None,
        priority: int = 0
    ) -> Optional[Dict[str, Any]]:
        """调度设备"""
        try:
            # 查找可用设备
            query = Device.query.filter_by(
                device_type=device_type,
                is_active=True,
                status='online'
            )
            
            if slave_id:
                query = query.filter_by(slave_id=slave_id)
                
            # 检查设备是否正在使用
            available_devices = []
            for device in query.all():
                usage = DeviceUsage.query.filter_by(
                    device_id=device.id,
                    end_time=None
                ).first()
                
                if not usage:
                    available_devices.append(device)
                    
            if not available_devices:
                logger.error(f"No available devices of type: {device_type}")
                return None
                
            # 选择设备(这里可以实现更复杂的调度算法)
            device = available_devices[0]
            
            # 使用设备
            usage = device_manager.use_device(
                device_id=device.id,
                user_id=user_id,
                description=f"Scheduled usage with priority {priority}"
            )
            
            if not usage:
                return None
                
            # 如果指定了使用时长,设置自动释放
            if duration:
                # TODO: 实现定时释放逻辑
                pass
                
            logger.info(
                f"Device scheduled: {device.name} -> User {user_id}"
            )
            return cast(Dict[str, Any], usage)
            
        except Exception as e:
            logger.error(f"Failed to schedule device: {e}")
            return None
    
    def release_scheduled_device(
        self,
        device_id: int,
        user_id: int
    ) -> bool:
        """释放调度的设备"""
        try:
            return device_manager.release_device(device_id, user_id)
            
        except Exception as e:
            logger.error(f"Failed to release scheduled device: {e}")
            return False
    
    def get_device_schedule(
        self,
        device_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """获取设备调度计划"""
        try:
            query = DeviceUsage.query.filter_by(device_id=device_id)
            
            if start_date:
                query = query.filter(DeviceUsage.start_time >= start_date)
            if end_date:
                query = query.filter(DeviceUsage.start_time <= end_date)
                
            schedule = query.order_by(
                desc(DeviceUsage.start_time)
            ).all()
            
            return [cast(Dict[str, Any], usage.to_dict()) for usage in schedule]
            
        except Exception as e:
            logger.error(f"Failed to get device schedule: {e}")
            return []
    
    def get_user_schedule(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """获取用户调度计划"""
        try:
            query = DeviceUsage.query.filter_by(user_id=user_id)
            
            if start_date:
                query = query.filter(DeviceUsage.start_time >= start_date)
            if end_date:
                query = query.filter(DeviceUsage.start_time <= end_date)
                
            schedule = query.order_by(
                desc(DeviceUsage.start_time)
            ).all()
            
            return [cast(Dict[str, Any], usage.to_dict()) for usage in schedule]
            
        except Exception as e:
            logger.error(f"Failed to get user schedule: {e}")
            return []
    
    def check_device_availability(
        self,
        device_type: str,
        start_time: datetime,
        end_time: datetime,
        slave_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """检查设备可用性"""
        try:
            # 查找指定类型的设备
            query = Device.query.filter_by(
                device_type=device_type,
                is_active=True
            )
            
            if slave_id:
                query = query.filter_by(slave_id=slave_id)
                
            devices = query.all()
            if not devices:
                return []
                
            # 检查每个设备在指定时间段的使用情况
            available_devices = []
            for device in devices:
                # 检查是否有重叠的使用记录
                conflicts = DeviceUsage.query.filter(
                    DeviceUsage.device_id == device.id,
                    DeviceUsage.start_time < end_time,
                    (
                        DeviceUsage.end_time.is_(None) |
                        (DeviceUsage.end_time > start_time)
                    )
                ).all()
                
                if not conflicts:
                    available_devices.append({
                        'device_id': device.id,
                        'name': device.name,
                        'slave_id': device.slave_id,
                        'status': device.status
                    })
                    
            return available_devices
            
        except Exception as e:
            logger.error(f"Failed to check device availability: {e}")
            return []
    
    def get_scheduling_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取调度统计信息"""
        try:
            query = DeviceUsage.query
            
            if start_date:
                query = query.filter(DeviceUsage.start_time >= start_date)
            if end_date:
                query = query.filter(DeviceUsage.start_time <= end_date)
                
            # 总调度次数
            total_schedules = query.count()
            
            # 按设备类型统计
            device_type_stats: Dict[str, int] = {}
            for device in Device.query.all():
                count = query.filter_by(device_id=device.id).count()
                if device.device_type in device_type_stats:
                    device_type_stats[device.device_type] += count
                else:
                    device_type_stats[device.device_type] = count
                    
            # 按用户统计
            user_stats: Dict[int, int] = {}
            for usage in query.all():
                if usage.user_id in user_stats:
                    user_stats[usage.user_id] += 1
                else:
                    user_stats[usage.user_id] = 1
                    
            # 平均使用时长
            total_hours = 0
            completed_schedules = 0
            for usage in query.filter(DeviceUsage.end_time.isnot(None)).all():
                if usage.end_time:  # 类型检查器需要这个检查
                    duration = (usage.end_time - usage.start_time).total_seconds()
                    total_hours += duration / 3600
                    completed_schedules += 1
                
            avg_duration = (
                total_hours / completed_schedules
                if completed_schedules > 0
                else 0
            )
            
            return {
                'total_schedules': total_schedules,
                'completed_schedules': completed_schedules,
                'device_type_stats': device_type_stats,
                'user_stats': user_stats,
                'avg_duration': round(avg_duration, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get scheduling stats: {e}")
            return {
                'total_schedules': 0,
                'completed_schedules': 0,
                'device_type_stats': {},
                'user_stats': {},
                'avg_duration': 0
            } 