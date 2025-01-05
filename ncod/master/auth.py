from typing import Dict, Optional
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from .models import User, db
from .utils.redis_cache import cache
from .utils.logger import get_logger

logger = get_logger(__name__)


def authenticate_user(username: str, password: str, client_type: str = 'web') -> Optional[Dict]:
    """验证用户登录
    Args:
        username: 用户名
        password: 密码
        client_type: 客户端类型 ('web' 或 'client')
    """
    try:
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return None
            
        if not user.is_active:
            logger.warning(f"Inactive user attempted login: {username}")
            return None
            
        # 仅对客户端登录验证MAC地址
        if client_type == 'client':
            if not user.mac_address:
                logger.warning(f"Client login without MAC address: {username}")
                return None
                
            current_mac = get_client_mac_address()
            if not current_mac or current_mac != user.mac_address:
                logger.warning(f"MAC address mismatch for user: {username}")
                return None
            
        # 生成访问令牌
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=1)
        )
        
        # 更新用户信息
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'organization': user.organization,
            'role': user.role,
            'mac_address': user.mac_address,
            'access_token': access_token,
            'client_type': client_type
        }
        
        # 缓存用户信息
        cache.set(
            f'user_info_{user.id}',
            user_info,
            timeout=3600  # 1小时
        )
        
        logger.info(f"User {username} logged in successfully via {client_type}")
        return user_info
        
    except Exception as e:
        logger.error(f"Authentication failed for user {username}: {e}")
        return None


def verify_mac_address(mac_address: str) -> bool:
    """验证MAC地址"""
    try:
        # 检查MAC地址格式
        if not is_valid_mac_format(mac_address):
            logger.warning(f"Invalid MAC address format: {mac_address}")
            return False
            
        # 检查MAC地址是否已注册
        user = User.query.filter_by(mac_address=mac_address).first()
        if not user:
            logger.warning(f"Unregistered MAC address: {mac_address}")
            return False
            
        if not user.is_active:
            logger.warning(f"MAC address belongs to inactive user: {mac_address}")
            return False
            
        logger.info(f"MAC address verified: {mac_address}")
        return True
        
    except Exception as e:
        logger.error(f"MAC address verification failed: {e}")
        return False


def is_valid_mac_format(mac_address: str) -> bool:
    """检查MAC地址格式"""
    try:
        # 移除所有分隔符
        mac = mac_address.replace(':', '').replace('-', '')
        
        # 检查长度
        if len(mac) != 12:
            return False
            
        # 检查是否为有效的十六进制字符
        return all(c in '0123456789ABCDEFabcdef' for c in mac)
        
    except Exception:
        return False


def register_user(
    username: str,
    password: str,
    email: str,
    organization: Optional[str] = None,
    mac_address: Optional[str] = None
) -> Optional[Dict]:
    """注册新用户"""
    try:
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            logger.warning(f"Username already exists: {username}")
            return None
            
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            logger.warning(f"Email already exists: {email}")
            return None
            
        # 检查MAC地址是否已存在
        if mac_address and User.query.filter_by(mac_address=mac_address).first():
            logger.warning(f"MAC address already exists: {mac_address}")
            return None
            
        # 创建新用户
        user = User(
            username=username,
            email=email,
            organization=organization,
            mac_address=mac_address,
            created_at=datetime.utcnow()
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User registered successfully: {username}")
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'organization': user.organization,
            'role': user.role,
            'mac_address': user.mac_address
        }
        
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        db.session.rollback()
        return None


def change_password(user_id: int, old_password: str, new_password: str) -> bool:
    """修改用户密码"""
    try:
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return False
            
        # 验证旧密码
        if not user.check_password(old_password):
            logger.warning(f"Invalid old password for user: {user_id}")
            return False
            
        # 设置新密码
        user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"Password changed for user: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Password change failed for user {user_id}: {e}")
        db.session.rollback()
        return False


def reset_password(user_id: int, new_password: str) -> bool:
    """重置用户密码"""
    try:
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return False
            
        # 设置新密码
        user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"Password reset for user: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Password reset failed for user {user_id}: {e}")
        db.session.rollback()
        return False


def deactivate_user(user_id: int) -> bool:
    """停用用户"""
    try:
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return False
            
        user.is_active = False
        db.session.commit()
        
        # 清除用户缓存
        cache.delete(f'user_info_{user_id}')
        
        logger.info(f"User deactivated: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"User deactivation failed: {e}")
        db.session.rollback()
        return False


def activate_user(user_id: int) -> bool:
    """启用用户"""
    try:
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return False
            
        user.is_active = True
        db.session.commit()
        
        logger.info(f"User activated: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"User activation failed: {e}")
        db.session.rollback()
        return False
