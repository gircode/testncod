"""Slave模块"""

from datetime import datetime

from app.core.database import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship


class Slave(Base):
    __tablename__ = "slaves"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    ip_address = Column(String, unique=True, index=True)
    api_key = Column(String, unique=True)
    status = Column(String, default="offline")
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    devices = relationship("Device", back_populates="slave")
    alerts = relationship("Alert", back_populates="slave")
