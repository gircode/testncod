"""Alert模块"""

from datetime import datetime

from app.core.database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)  # error, warning, info
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(String, nullable=True)

    # Foreign keys
    device_id = Column(Integer, ForeignKey("devices.id"))
    slave_id = Column(Integer, ForeignKey("slaves.id"))

    # Relationships
    device = relationship("Device", back_populates="alerts")
    slave = relationship("Slave", back_populates="alerts")
