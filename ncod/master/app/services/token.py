"""
令牌服务
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.token import Token
from ..models.user import User


class TokenService:
    """令牌服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_token(
        self, user_id: int, token_type: str, expires_in: timedelta
    ) -> Token:
        """
        创建令牌

        Args:
            user_id: 用户ID
            token_type: 令牌类型 (password_reset, email_verification)
            expires_in: 过期时间
        """
        # 创建令牌
        token = Token(
            token=str(uuid4()),
            user_id=user_id,
            type=token_type,
            expires_at=datetime.utcnow() + expires_in,
        )
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def verify_token(self, token: str, token_type: str) -> Optional[User]:
        """
        验证令牌

        Args:
            token: 令牌字符串
            token_type: 令牌类型
        """
        # 查找令牌
        stmt = (
            select(Token)
            .where(
                and_(
                    Token.token == token,
                    Token.type == token_type,
                    Token.expires_at > datetime.utcnow(),
                    Token.is_used == False,
                )
            )
            .join(Token.user)
        )

        result = await self.db.execute(stmt)
        token_obj = result.scalar_one_or_none()

        if not token_obj:
            return None

        # 标记令牌为已使用
        token_obj.is_used = True
        self.db.add(token_obj)
        await self.db.commit()

        return token_obj.user

    async def create_password_reset_token(self, user: User) -> str:
        """创建密码重置令牌"""
        # 删除该用户的所有未过期重置令牌
        await self.delete_password_reset_tokens(user.id)

        # 创建新令牌
        token = await self.create_token(
            user_id=user.id, token_type="password_reset", expires_in=timedelta(hours=24)
        )
        return token.token

    async def verify_password_reset_token(self, token: str) -> Optional[User]:
        """验证密码重置令牌"""
        return await self.verify_token(token, "password_reset")

    async def create_email_verification_token(self, user: User) -> str:
        """创建邮箱验证令牌"""
        # 删除该用户的所有未过期验证令牌
        await self.delete_email_verification_tokens(user.id)

        # 创建新令牌
        token = await self.create_token(
            user_id=user.id,
            token_type="email_verification",
            expires_in=timedelta(hours=24),
        )
        return token.token

    async def verify_email_verification_token(self, token: str) -> Optional[User]:
        """验证邮箱验证令牌"""
        return await self.verify_token(token, "email_verification")

    async def delete_expired_tokens(self) -> None:
        """删除所有过期令牌"""
        stmt = select(Token).where(
            or_(Token.expires_at <= datetime.utcnow(), Token.is_used == True)
        )
        result = await self.db.execute(stmt)
        expired_tokens = result.scalars().all()

        for token in expired_tokens:
            await self.db.delete(token)
        await self.db.commit()

    async def delete_user_tokens(self, user_id: int) -> None:
        """删除用户的所有令牌"""
        stmt = select(Token).where(Token.user_id == user_id)
        result = await self.db.execute(stmt)
        tokens = result.scalars().all()

        for token in tokens:
            await self.db.delete(token)
        await self.db.commit()

    async def delete_password_reset_tokens(self, user_id: int) -> None:
        """删除用户的所有密码重置令牌"""
        stmt = select(Token).where(
            and_(Token.user_id == user_id, Token.type == "password_reset")
        )
        result = await self.db.execute(stmt)
        tokens = result.scalars().all()

        for token in tokens:
            await self.db.delete(token)
        await self.db.commit()

    async def delete_email_verification_tokens(self, user_id: int) -> None:
        """删除用户的所有邮箱验证令牌"""
        stmt = select(Token).where(
            and_(Token.user_id == user_id, Token.type == "email_verification")
        )
        result = await self.db.execute(stmt)
        tokens = result.scalars().all()

        for token in tokens:
            await self.db.delete(token)
        await self.db.commit()
