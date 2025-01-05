"""用户服务"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.user import User, UserCreate, UserUpdate
from ..core.security import get_password_hash, verify_password
from ..utils.logger import logger


class UserService:
    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        """获取用户信息"""
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """创建新用户"""
        try:
            # 检查用户名是否已存在
            if self.get_user_by_username(db, user_data.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered",
                )

            # 创建用户
            hashed_password = get_password_hash(user_data.password)
            db_user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except Exception as e:
            db.rollback()
            logger.error("创建用户失败", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create user"
            )

    def update_last_login(self, db: Session, user: User) -> None:
        """更新最后登录时间"""
        try:
            user.last_login = datetime.utcnow()
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("更新登录时间失败", exc_info=True)

    def update_user(
        self, db: Session, user_id: int, user_data: UserUpdate
    ) -> Optional[User]:
        """更新用户信息"""
        try:
            user = self.get_user(db, user_id)
            if not user:
                return None

            # 更新用户信息
            if user_data.username is not None:
                user.username = user_data.username
            if user_data.email is not None:
                user.email = user_data.email
            if user_data.password is not None:
                user.hashed_password = get_password_hash(user_data.password)
            if user_data.is_active is not None:
                user.is_active = user_data.is_active

            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            logger.error("更新用户信息失败", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update user"
            )
