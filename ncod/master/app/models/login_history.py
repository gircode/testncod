"""
登录历史记录模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class LoginHistory(Base):
    """登录历史记录"""

    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    success = Column(Boolean, default=True, nullable=False)
    ip_address = Column(String(50), nullable=False)
    user_agent = Column(String(255), nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联关系
    user = relationship("User", back_populates="login_history")
