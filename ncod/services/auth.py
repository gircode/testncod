from sqlalchemy.orm import Session
from typing import Optional
from ..models.user import User
from ..core.security import get_password_hash, verify_password, validate_password
from ..utils.logger import logger
from fastapi import HTTPException


class AuthService:
    def authenticate_user(
        self, db: Session, username: str, password: str
    ) -> Optional[User]:
        """验证用户"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def verify_mac_address(self, user_id: int, mac_address: str) -> bool:
        """验证MAC地址"""
        # TODO: 实现MAC地址验证逻辑
        return True

    def register_mac_address(self, user_id: int, mac_address: str) -> None:
        """注册MAC地址"""
        # TODO: 实现MAC地址注册逻辑
        pass

    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """创建新用户"""
        try:
            # 验证密码强度
            if not validate_password(user_data.password):
                raise HTTPException(
                    status_code=400,
                    detail="Password does not meet security requirements",
                )

            # 检查用户名是否已存在
            if db.query(User).filter(User.username == user_data.username).first():
                raise HTTPException(
                    status_code=400, detail="Username already registered"
                )

            # 检查邮箱是否已存在
            if db.query(User).filter(User.email == user_data.email).first():
                raise HTTPException(status_code=400, detail="Email already registered")

            # 创建新用户
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
            logger.error(f"创建用户失败: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to create user")
