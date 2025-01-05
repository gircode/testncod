"""组织架构数据库模型"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from ncod.core.db.base import Base


class Group(Base):
    """大组模型"""

    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    departments = relationship("Department", back_populates="group")
    devices = relationship("Device", back_populates="group")


class Department(Base):
    """部门模型"""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"))
    level = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = relationship("Group", back_populates="departments")
    parent = relationship("Department", remote_side=[id])
    users = relationship("User", back_populates="department")
