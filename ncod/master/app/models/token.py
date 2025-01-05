"""
令牌模型
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base

if TYPE_CHECKING:
    from .user import User


class Token(Base):
    """令牌模型"""

    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(50))  # password_reset, email_verification
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="tokens")

    def __repr__(self) -> str:
        return f"<Token {self.token} ({self.type})>"
