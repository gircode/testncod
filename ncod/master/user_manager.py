from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import desc
from .models import db, User
from .utils.logger import get_logger
from .config_manager import ConfigManager

logger = get_logger(__name__)
config = ConfigManager()


class UserManager:
    _instance: Optional['UserManager'] = None
    
    def __new__(cls) -> 'UserManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_user(
        self,
        username: str,
        password: str,
        email: str,
        role: str = 'user',
        is_active: bool = True
    ) -> Optional[Dict[str, Any]]:
        """创建用户"""
        try:
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                logger.error(f"Username already exists: {username}")
                return None
                
            # 检查邮箱是否已存在
            if User.query.filter_by(email=email).first():
                logger.error(f"Email already exists: {email}")
                return None
                
            # 创建用户
            user = User(
                username=username,
                password=generate_password_hash(password),
                email=email,
                role=role,
                is_active=is_active,
                created_at=datetime.now()
            )
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"User created: {username}")
            return cast(Dict[str, Any], user.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            db.session.rollback()
            return None
    
    def get_user(
        self,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        try:
            query = User.query
            
            if user_id:
                query = query.filter_by(id=user_id)
            elif username:
                query = query.filter_by(username=username)
            elif email:
                query = query.filter_by(email=email)
            else:
                logger.error("No search criteria provided")
                return None
                
            user = query.first()
            return cast(Dict[str, Any], user.to_dict()) if user else None
            
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    def update_user(
        self,
        user_id: int,
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """更新用户信息"""
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return None
                
            # 更新密码
            if 'password' in kwargs:
                kwargs['password'] = generate_password_hash(
                    kwargs['password']
                )
                
            # 更新其他字段
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
                    
            user.updated_at = datetime.now()
            db.session.commit()
            
            logger.info(f"User updated: {user.username}")
            return cast(Dict[str, Any], user.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            db.session.rollback()
            return None
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
                
            db.session.delete(user)
            db.session.commit()
            
            logger.info(f"User deleted: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            db.session.rollback()
            return False
    
    def verify_password(
        self,
        username: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """验证用户密码"""
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                logger.error(f"User not found: {username}")
                return None
                
            if not check_password_hash(user.password, password):
                logger.error(f"Invalid password for user: {username}")
                return None
                
            if not user.is_active:
                logger.error(f"User is inactive: {username}")
                return None
                
            return cast(Dict[str, Any], user.to_dict())
            
        except Exception as e:
            logger.error(f"Failed to verify password: {e}")
            return None
    
    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> bool:
        """修改用户密码"""
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
                
            if not check_password_hash(user.password, old_password):
                logger.error(f"Invalid old password for user: {user.username}")
                return False
                
            user.password = generate_password_hash(new_password)
            user.updated_at = datetime.now()
            db.session.commit()
            
            logger.info(f"Password changed for user: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to change password: {e}")
            db.session.rollback()
            return False
    
    def reset_password(
        self,
        user_id: int,
        new_password: str
    ) -> bool:
        """重置用户密码"""
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
                
            user.password = generate_password_hash(new_password)
            user.updated_at = datetime.now()
            db.session.commit()
            
            logger.info(f"Password reset for user: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset password: {e}")
            db.session.rollback()
            return False
    
    def activate_user(self, user_id: int) -> bool:
        """激活用户"""
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
                
            user.is_active = True
            user.updated_at = datetime.now()
            db.session.commit()
            
            logger.info(f"User activated: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate user: {e}")
            db.session.rollback()
            return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """停用用户"""
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
                
            user.is_active = False
            user.updated_at = datetime.now()
            db.session.commit()
            
            logger.info(f"User deactivated: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate user: {e}")
            db.session.rollback()
            return False
    
    def list_users(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出用户"""
        try:
            query = User.query
            
            if role:
                query = query.filter_by(role=role)
            if is_active is not None:
                query = query.filter_by(is_active=is_active)
                
            users = query.order_by(
                desc(User.created_at)
            ).offset(offset).limit(limit).all()
            
            return cast(List[Dict[str, Any]], [user.to_dict() for user in users])
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []
    
    def search_users(
        self,
        keyword: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """搜索用户"""
        try:
            users = User.query.filter(
                (User.username.ilike(f"%{keyword}%")) |
                (User.email.ilike(f"%{keyword}%"))
            ).order_by(
                desc(User.created_at)
            ).offset(offset).limit(limit).all()
            
            return cast(List[Dict[str, Any]], [user.to_dict() for user in users])
            
        except Exception as e:
            logger.error(f"Failed to search users: {e}")
            return []
    
    def count_users(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """统计用户数量"""
        try:
            query = User.query
            
            if role:
                query = query.filter_by(role=role)
            if is_active is not None:
                query = query.filter_by(is_active=is_active)
                
            return query.count()
            
        except Exception as e:
            logger.error(f"Failed to count users: {e}")
            return 0 