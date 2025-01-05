"""认证相关数据库模型"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from ncod.core.db import Base


class UserMACAddress(Base):
    """用户MAC地址模型"""

    __tablename__ = "user_mac_addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mac_address = Column(String(17), nullable=False, unique=True)
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系
    user = relationship("User", back_populates="mac_addresses")

    def __str__(self) -> str:
        """字符串表示"""
        return f"UserMACAddress(id={self.id}, mac_address={self.mac_address})"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "mac_address": self.mac_address,
            "registered_at": self.registered_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class UserToken(Base):
    """用户令牌模型"""

    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), nullable=False, unique=True)
    token_type = Column(String(20), nullable=False)  # access 或 refresh
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系
    user = relationship("User")

    def __str__(self) -> str:
        """字符串表示"""
        return f"UserToken(id={self.id}, token_type={self.token_type})"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat(),
            "is_revoked": self.is_revoked,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
