from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ncod.core.db.base import Base


class UserAssignment(Base):
    __tablename__ = "user_assignments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    assigner_id = Column(Integer, ForeignKey("users.id"))
    remark = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    organization = relationship("Organization")
    assigner = relationship("User", foreign_keys=[assigner_id])
