"""
审计日志模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class AuditLog(Base):
    """审计日志模型"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # success, failure, error
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    resource_type = Column(String(50))  # user, role, device, etc.
    resource_id = Column(String(50))
    details = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联关系
    user = relationship("User", backref="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by user {self.user_id} at {self.created_at}>"
