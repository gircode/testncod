from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from sqlalchemy.sql import desc
from sqlalchemy.sql.functions import count
from .models import db, Device, DeviceUsage
from .utils.logger import get_logger
from .config_manager import ConfigManager

logger = get_logger(__name__)
config = ConfigManager()


class DeviceManager:
    _instance: Optional['DeviceManager'] = None
    
    def __new__(cls) -> 'DeviceManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_device(
        self,
        name: str,
        device_type: str,
        slave_id: int,
        description: str = '',
        is_active: bool = True
    ) -> Optional[Dict[str, Any]]:
        """注册设备"""
        try:
            # 检查设备名是否已存在
            if Device.query.filter_by(name=name).first():
                logger.error(f"Device name already exists: {name}")
                return None
                
            # 创建设备
            device = Device(
                name=name,
                device_type=device_type,
                slave_id=slave_id,
                description=description,
                is_active=is_active,
                status='offline',
                created_at=datetime.now()
            )
            
            db.session.add(device)
            db.session.commit()
            
            logger.info(f"Device registered: {name}")
            return cast(Dict[str, Any], device.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            db.session.rollback()
            return None
    
    def get_device(
        self,
        device_id: Optional[int] = None,
        name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取设备信息"""
        try:
            query = Device.query
            
            if device_id:
                query = query.filter_by(id=device_id)
            elif name:
                query = query.filter_by(name=name)
            else:
                logger.error("No search criteria provided")
                return None
                
            device = query.first()
            return cast(Dict[str, Any], device.to_dict()) if device else None
            
        except Exception as e:
            logger.error(f"Failed to get device: {e}")
            return None
    
    def update_device(
        self,
        device_id: int,
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """更新设备信息"""
        try:
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return None
                
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(device, key):
                    setattr(device, key, value)
                    
            device.updated_at = datetime.now()
            db.session.commit()
            
            logger.info(f"Device updated: {device.name}")
            return cast(Dict[str, Any], device.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to update device: {e}")
            db.session.rollback()
            return None
    
    def delete_device(self, device_id: int) -> bool:
        """删除设备"""
        try:
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return False
                
            db.session.delete(device)
            db.session.commit()
            
            logger.info(f"Device deleted: {device.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete device: {e}")
            db.session.rollback()
            return False
    
    def update_device_status(
        self,
        device_id: int,
        status: str,
        message: str = ''
    ) -> bool:
        """更新设备状态"""
        try:
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return False
                
            device.status = status
            device.status_message = message
            device.updated_at = datetime.now()
            db.session.commit()
            
            logger.info(f"Device status updated: {device.name} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update device status: {e}")
            db.session.rollback()
            return False
    
    def use_device(
        self,
        device_id: int,
        user_id: int,
        description: str = ''
    ) -> Optional[Dict[str, Any]]:
        """使用设备"""
        try:
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return None
                
            if not device.is_active:
                logger.error(f"Device is inactive: {device.name}")
                return None
                
            if device.status != 'online':
                logger.error(f"Device is not online: {device.name}")
                return None
                
            # 检查设备是否已被占用
            current_usage = DeviceUsage.query.filter_by(
                device_id=device_id,
                end_time=None
            ).first()
            
            if current_usage:
                logger.error(f"Device is in use: {device.name}")
                return None
                
            # 创建使用记录
            usage = DeviceUsage(
                device_id=device_id,
                user_id=user_id,
                description=description,
                start_time=datetime.now()
            )
            
            db.session.add(usage)
            db.session.commit()
            
            logger.info(f"Device usage started: {device.name}")
            return cast(Dict[str, Any], usage.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to use device: {e}")
            db.session.rollback()
            return None
    
    def release_device(
        self,
        device_id: int,
        user_id: int
    ) -> bool:
        """释放设备"""
        try:
            usage = DeviceUsage.query.filter_by(
                device_id=device_id,
                user_id=user_id,
                end_time=None
            ).first()
            
            if not usage:
                logger.error(f"Device usage not found: {device_id}")
                return False
                
            usage.end_time = datetime.now()
            db.session.commit()
            
            logger.info(f"Device released: {usage.device.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to release device: {e}")
            db.session.rollback()
            return False
    
    def list_devices(
        self,
        device_type: Optional[str] = None,
        slave_id: Optional[int] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出设备"""
        try:
            query = Device.query
            
            if device_type:
                query = query.filter_by(device_type=device_type)
            if slave_id:
                query = query.filter_by(slave_id=slave_id)
            if status:
                query = query.filter_by(status=status)
            if is_active is not None:
                query = query.filter_by(is_active=is_active)
                
            devices = query.order_by(
                desc(Device.created_at)
            ).offset(offset).limit(limit).all()
            
            return cast(List[Dict[str, Any]], [
                device.to_dict() for device in devices
            ])
            
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
            return []
    
    def search_devices(
        self,
        keyword: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """搜索设备"""
        try:
            devices = Device.query.filter(
                (Device.name.ilike(f"%{keyword}%")) |
                (Device.description.ilike(f"%{keyword}%"))
            ).order_by(
                desc(Device.created_at)
            ).offset(offset).limit(limit).all()
            
            return cast(List[Dict[str, Any]], [
                device.to_dict() for device in devices
            ])
            
        except Exception as e:
            logger.error(f"Failed to search devices: {e}")
            return []
    
    def get_device_usage_history(
        self,
        device_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取设备使用历史"""
        try:
            usages = DeviceUsage.query.filter_by(
                device_id=device_id
            ).order_by(
                desc(DeviceUsage.start_time)
            ).offset(offset).limit(limit).all()
            
            return cast(List[Dict[str, Any]], [
                usage.to_dict() for usage in usages
            ])
            
        except Exception as e:
            logger.error(f"Failed to get device usage history: {e}")
            return []
    
    def get_user_device_usage(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取用户设备使用记录"""
        try:
            usages = DeviceUsage.query.filter_by(
                user_id=user_id
            ).order_by(
                desc(DeviceUsage.start_time)
            ).offset(offset).limit(limit).all()
            
            return cast(List[Dict[str, Any]], [
                usage.to_dict() for usage in usages
            ])
            
        except Exception as e:
            logger.error(f"Failed to get user device usage: {e}")
            return []
    
    def count_devices(
        self,
        device_type: Optional[str] = None,
        slave_id: Optional[int] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """统计设备数量"""
        try:
            query = Device.query
            
            if device_type:
                query = query.filter_by(device_type=device_type)
            if slave_id:
                query = query.filter_by(slave_id=slave_id)
            if status:
                query = query.filter_by(status=status)
            if is_active is not None:
                query = query.filter_by(is_active=is_active)
                
            result = query.with_entities(count(Device.id)).scalar()
            return cast(int, result) if result is not None else 0
            
        except Exception as e:
            logger.error(f"Failed to count devices: {e}")
            return 0 