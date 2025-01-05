from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from sqlalchemy.sql import desc
from .models import db, Device, DevicePermission as PermissionModel
from .utils.logger import get_logger
from .config_manager import ConfigManager

logger = get_logger(__name__)
config = ConfigManager()


class DevicePermissionManager:
    _instance: Optional['DevicePermissionManager'] = None
    
    def __new__(cls) -> 'DevicePermissionManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def grant_permission(
        self,
        device_id: int,
        user_id: int,
        permission_type: str,
        expires_at: Optional[datetime] = None,
        granted_by: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """授予设备权限"""
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"Device not found: {device_id}")
                return None
                
            # 检查是否已有权限
            existing = PermissionModel.query.filter_by(
                device_id=device_id,
                user_id=user_id,
                permission_type=permission_type,
                is_active=True
            ).first()
            
            if existing:
                logger.error(
                    f"Permission already exists: {device_id} -> {user_id}"
                )
                return cast(Dict[str, Any], existing.to_dict())
                
            # 创建权限记录
            permission = PermissionModel(
                device_id=device_id,
                user_id=user_id,
                permission_type=permission_type,
                expires_at=expires_at,
                granted_by=granted_by,
                is_active=True,
                created_at=datetime.now()
            )
            
            db.session.add(permission)
            db.session.commit()
            
            logger.info(
                f"Permission granted: {device.name} -> User {user_id}"
            )
            return cast(Dict[str, Any], permission.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to grant permission: {e}")
            db.session.rollback()
            return None
    
    def revoke_permission(
        self,
        permission_id: int,
        revoked_by: Optional[int] = None
    ) -> bool:
        """撤销设备权限"""
        try:
            permission = PermissionModel.query.get(permission_id)
            if not permission:
                logger.error(f"Permission not found: {permission_id}")
                return False
                
            permission.is_active = False
            permission.revoked_by = revoked_by
            permission.revoked_at = datetime.now()
            permission.updated_at = datetime.now()
            
            db.session.commit()
            
            logger.info(f"Permission revoked: {permission_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke permission: {e}")
            db.session.rollback()
            return False
    
    def check_permission(
        self,
        device_id: int,
        user_id: int,
        permission_type: str
    ) -> bool:
        """检查设备权限"""
        try:
            # 检查是否有有效权限
            permission = PermissionModel.query.filter_by(
                device_id=device_id,
                user_id=user_id,
                permission_type=permission_type,
                is_active=True
            ).first()
            
            if not permission:
                return False
                
            # 检查是否过期
            if permission.expires_at and permission.expires_at < datetime.now():
                permission.is_active = False
                db.session.commit()
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to check permission: {e}")
            return False
    
    def list_user_permissions(
        self,
        user_id: int,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """列出用户权限"""
        try:
            query = PermissionModel.query.filter_by(user_id=user_id)
            
            if not include_inactive:
                query = query.filter_by(is_active=True)
                
            permissions = query.order_by(
                desc(PermissionModel.created_at)
            ).all()
            
            return [
                cast(Dict[str, Any], perm.to_dict()) for perm in permissions
            ]
            
        except Exception as e:
            logger.error(f"Failed to list user permissions: {e}")
            return []
    
    def list_device_permissions(
        self,
        device_id: int,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """列出设备权限"""
        try:
            query = PermissionModel.query.filter_by(device_id=device_id)
            
            if not include_inactive:
                query = query.filter_by(is_active=True)
                
            permissions = query.order_by(
                desc(PermissionModel.created_at)
            ).all()
            
            return [
                cast(Dict[str, Any], perm.to_dict()) for perm in permissions
            ]
            
        except Exception as e:
            logger.error(f"Failed to list device permissions: {e}")
            return []
    
    def get_permission_history(
        self,
        device_id: Optional[int] = None,
        user_id: Optional[int] = None,
        permission_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取权限历史"""
        try:
            query = PermissionModel.query
            
            if device_id:
                query = query.filter_by(device_id=device_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            if permission_type:
                query = query.filter_by(permission_type=permission_type)
            if start_date:
                query = query.filter(
                    PermissionModel.created_at >= start_date
                )
            if end_date:
                query = query.filter(
                    PermissionModel.created_at <= end_date
                )
                
            permissions = query.order_by(
                desc(PermissionModel.created_at)
            ).offset(offset).limit(limit).all()
            
            return [
                cast(Dict[str, Any], perm.to_dict()) for perm in permissions
            ]
            
        except Exception as e:
            logger.error(f"Failed to get permission history: {e}")
            return []
    
    def get_permission_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取权限摘要"""
        try:
            query = PermissionModel.query
            
            if start_date:
                query = query.filter(
                    PermissionModel.created_at >= start_date
                )
            if end_date:
                query = query.filter(
                    PermissionModel.created_at <= end_date
                )
                
            # 总权限数
            total_permissions = query.count()
            
            # 活动权限数
            active_permissions = query.filter_by(is_active=True).count()
            
            # 按类型统计
            type_counts: Dict[str, int] = {}
            for perm_type in query.with_entities(
                PermissionModel.permission_type
            ).distinct().all():
                count = query.filter_by(
                    permission_type=perm_type[0]
                ).count()
                type_counts[perm_type[0]] = count
                
            # 按设备统计
            device_counts: Dict[int, int] = {}
            for device_id in query.with_entities(
                PermissionModel.device_id
            ).distinct().all():
                count = query.filter_by(device_id=device_id[0]).count()
                device_counts[device_id[0]] = count
                
            # 按用户统计
            user_counts: Dict[int, int] = {}
            for user_id in query.with_entities(
                PermissionModel.user_id
            ).distinct().all():
                count = query.filter_by(user_id=user_id[0]).count()
                user_counts[user_id[0]] = count
                
            return {
                'total_permissions': total_permissions,
                'active_permissions': active_permissions,
                'type_counts': type_counts,
                'device_counts': device_counts,
                'user_counts': user_counts
            }
            
        except Exception as e:
            logger.error(f"Failed to get permission summary: {e}")
            return {
                'total_permissions': 0,
                'active_permissions': 0,
                'type_counts': {},
                'device_counts': {},
                'user_counts': {}
            } 