"""认证服务"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from ncod.core.logger import setup_logger
from ncod.core.config import config
from ncod.master.services.user import user_service
from ncod.master.models.user import User

logger = setup_logger("auth_service")


class AuthService:
    """认证服务"""

    def __init__(self):
        self.user_service = user_service
        self.secret_key = config.jwt_secret_key
        self.algorithm = config.jwt_algorithm
        self.access_token_expire = config.access_token_expire_minutes
        self.refresh_token_expire = config.refresh_token_expire_days

    async def authenticate(
        self, username: str, password: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """用户认证"""
        try:
            # 获取用户
            async with self.user_service.transaction.transaction() as session:
                user = await User.get_by_username(session, username)
                if not user:
                    return False, "Invalid username or password", None

                # 验证密码
                if not self.user_service.verify_password(password, user.password_hash):
                    return False, "Invalid username or password", None

                # 检查用户状态
                if not user.is_active:
                    return False, "User is inactive", None

                # 更新登录信息
                await user.update_login()
                await session.commit()

                # 生成令牌
                access_token = self.create_access_token(user.id)
                refresh_token = self.create_refresh_token(user.id)

                return (
                    True,
                    "Login successful",
                    {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_type": "bearer",
                        "user": user.to_dict(),
                    },
                )

        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return False, str(e), None

    async def authenticate_mac(
        self, mac_address: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """MAC地址认证"""
        try:
            async with self.user_service.transaction.transaction() as session:
                user = await User.get_by_mac(session, mac_address)
                if not user:
                    return False, "Invalid MAC address", None

                if not user.is_active:
                    return False, "User is inactive", None

                # 更新登录信息
                await user.update_login()
                await session.commit()

                # 生成令牌
                access_token = self.create_access_token(user.id)

                return (
                    True,
                    "Login successful",
                    {
                        "access_token": access_token,
                        "token_type": "bearer",
                        "user": user.to_dict(),
                    },
                )

        except Exception as e:
            logger.error(f"Error authenticating MAC address: {e}")
            return False, str(e), None

    def create_access_token(self, user_id: str) -> str:
        """创建访问令牌"""
        try:
            expires_delta = timedelta(minutes=self.access_token_expire)
            expire = datetime.utcnow() + expires_delta

            to_encode = {"sub": user_id, "exp": expire, "type": "access"}
            return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise

    def create_refresh_token(self, user_id: str) -> str:
        """创建刷新令牌"""
        try:
            expires_delta = timedelta(days=self.refresh_token_expire)
            expire = datetime.utcnow() + expires_delta

            to_encode = {"sub": user_id, "exp": expire, "type": "refresh"}
            return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise

    async def refresh_token(
        self, refresh_token: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """刷新令牌"""
        try:
            # 验证刷新令牌
            payload = jwt.decode(
                refresh_token, self.secret_key, algorithms=[self.algorithm]
            )

            if payload.get("type") != "refresh":
                return False, "Invalid token type", None

            user_id = payload.get("sub")
            if not user_id:
                return False, "Invalid token", None

            # 获取用户
            user_data = await self.user_service.get_user(user_id)
            if not user_data:
                return False, "User not found", None

            # 生成新的访问令牌
            access_token = self.create_access_token(user_id)

            return (
                True,
                "Token refreshed",
                {"access_token": access_token, "token_type": "bearer"},
            )

        except jwt.ExpiredSignatureError:
            return False, "Token has expired", None
        except jwt.JWTError:
            return False, "Invalid token", None
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return False, str(e), None

    def verify_token(self, token: str) -> Tuple[bool, str, Optional[str]]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            user_id = payload.get("sub")
            if not user_id:
                return False, "Invalid token", None

            return True, "Token is valid", user_id

        except jwt.ExpiredSignatureError:
            return False, "Token has expired", None
        except jwt.JWTError:
            return False, "Invalid token", None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return False, str(e), None


# 创建全局认证服务实例
auth_service = AuthService()
