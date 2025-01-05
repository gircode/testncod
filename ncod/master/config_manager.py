from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from sqlalchemy.sql import desc
from .models import db, Device, DeviceConfig
from .utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    _instance: Optional['ConfigManager'] = None
    _config_cache: Dict[str, Any] = {}
    _cache_timestamp: Optional[datetime] = None
    _cache_ttl: int = 300  # 缓存有效期(秒)
    
    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _refresh_cache(self) -> None:
        """刷新配置缓存"""
        try:
            # 获取所有配置
            configs = DeviceConfig.query.all()
            
            # 更新缓存
            self._config_cache = {}
            for config in configs:
                if config.config_type not in self._config_cache:
                    self._config_cache[config.config_type] = {}
                self._config_cache[config.config_type][config.key] = config.value
                
            self._cache_timestamp = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to refresh config cache: {e}")
    
    def _check_cache(self) -> None:
        """检查缓存是否需要刷新"""
        if (
            not self._cache_timestamp or
            (datetime.now() - self._cache_timestamp).total_seconds() >
            self._cache_ttl
        ):
            self._refresh_cache()
    
    def get_device_thresholds(
        self,
        device_id: int
    ) -> Optional[Dict[str, float]]:
        """获取设备阈值配置"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return None
                
            # 获取设备类型的默认阈值
            self._check_cache()
            default_thresholds = self._config_cache.get(
                'device_thresholds',
                {}
            ).get(device.device_type, {})
            
            # 获取设备特定的阈值
            device_config = DeviceConfig.query.filter_by(
                device_id=device_id,
                config_type='thresholds'
            ).first()
            
            device_thresholds = device_config.value if device_config else {}
            
            # 合并阈值配置
            thresholds = {
                'cpu_threshold': float(
                    device_thresholds.get(
                        'cpu_threshold',
                        default_thresholds.get('cpu_threshold', 90.0)
                    )
                ),
                'memory_threshold': float(
                    device_thresholds.get(
                        'memory_threshold',
                        default_thresholds.get('memory_threshold', 90.0)
                    )
                ),
                'disk_threshold': float(
                    device_thresholds.get(
                        'disk_threshold',
                        default_thresholds.get('disk_threshold', 90.0)
                    )
                ),
                'network_threshold': float(
                    device_thresholds.get(
                        'network_threshold',
                        default_thresholds.get('network_threshold', 90.0)
                    )
                ),
                'temperature_threshold': float(
                    device_thresholds.get(
                        'temperature_threshold',
                        default_thresholds.get('temperature_threshold', 80.0)
                    )
                )
            }
            
            return thresholds
            
        except Exception as e:
            logger.error(f"Failed to get device thresholds: {e}")
            return None
    
    def get_notification_config(self) -> Optional[Dict[str, Any]]:
        """获取通知配置"""
        try:
            self._check_cache()
            return self._config_cache.get('notification', {})
            
        except Exception as e:
            logger.error(f"Failed to get notification config: {e}")
            return None
    
    def get_sync_config(self) -> Optional[Dict[str, Any]]:
        """获取同步配置"""
        try:
            self._check_cache()
            return self._config_cache.get('sync', {})
            
        except Exception as e:
            logger.error(f"Failed to get sync config: {e}")
            return None
    
    def update_device_config(
        self,
        device_id: int,
        config_type: str,
        config_data: Dict[str, Any]
    ) -> bool:
        """更新设备配置"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return False
                
            # 获取或创建配置记录
            config = DeviceConfig.query.filter_by(
                device_id=device_id,
                config_type=config_type
            ).first()
            
            if config:
                # 更新现有配置
                config.value.update(config_data)
                config.updated_at = datetime.now()
            else:
                # 创建新配置
                config = DeviceConfig(
                    device_id=device_id,
                    config_type=config_type,
                    value=config_data,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.session.add(config)
                
            db.session.commit()
            
            # 刷新缓存
            self._refresh_cache()
            
            logger.info(
                f"Device config updated: {device.name} -> {config_type}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to update device config: {e}")
            db.session.rollback()
            return False
    
    def update_global_config(
        self,
        config_type: str,
        config_data: Dict[str, Any]
    ) -> bool:
        """更新全局配置"""
        try:
            # 获取或创建配置记录
            config = DeviceConfig.query.filter_by(
                device_id=None,
                config_type=config_type
            ).first()
            
            if config:
                # 更新现有配置
                config.value.update(config_data)
                config.updated_at = datetime.now()
            else:
                # 创建新配置
                config = DeviceConfig(
                    device_id=None,
                    config_type=config_type,
                    value=config_data,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.session.add(config)
                
            db.session.commit()
            
            # 刷新缓存
            self._refresh_cache()
            
            logger.info(f"Global config updated: {config_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update global config: {e}")
            db.session.rollback()
            return False
    
    def get_device_config(
        self,
        device_id: int,
        config_type: str
    ) -> Optional[Dict[str, Any]]:
        """获取设备配置"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return None
                
            # 获取配置记录
            config = DeviceConfig.query.filter_by(
                device_id=device_id,
                config_type=config_type
            ).first()
            
            return cast(Dict[str, Any], config.value) if config else None
            
        except Exception as e:
            logger.error(f"Failed to get device config: {e}")
            return None
    
    def get_global_config(
        self,
        config_type: str
    ) -> Optional[Dict[str, Any]]:
        """获取全局配置"""
        try:
            # 获取配置记录
            config = DeviceConfig.query.filter_by(
                device_id=None,
                config_type=config_type
            ).first()
            
            return cast(Dict[str, Any], config.value) if config else None
            
        except Exception as e:
            logger.error(f"Failed to get global config: {e}")
            return None
    
    def delete_device_config(
        self,
        device_id: int,
        config_type: str
    ) -> bool:
        """删除设备配置"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return False
                
            # 删除配置记录
            result = DeviceConfig.query.filter_by(
                device_id=device_id,
                config_type=config_type
            ).delete()
            
            if result > 0:
                db.session.commit()
                # 刷新缓存
                self._refresh_cache()
                
                logger.info(
                    f"Device config deleted: {device.name} -> {config_type}"
                )
                return True
            else:
                logger.warning(
                    f"No config found to delete: {device_id} -> {config_type}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete device config: {e}")
            db.session.rollback()
            return False
    
    def delete_global_config(self, config_type: str) -> bool:
        """删除全局配置"""
        try:
            # 删除配置记录
            result = DeviceConfig.query.filter_by(
                device_id=None,
                config_type=config_type
            ).delete()
            
            if result > 0:
                db.session.commit()
                # 刷新缓存
                self._refresh_cache()
                
                logger.info(f"Global config deleted: {config_type}")
                return True
            else:
                logger.warning(f"No config found to delete: {config_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete global config: {e}")
            db.session.rollback()
            return False 