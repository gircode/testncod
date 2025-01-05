from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from ncod.core.db.database import Base


class DeviceHistory(Base):
    __tablename__ = "device_history"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(50))  # 'active', 'completed', 'terminated'

    device = relationship("Device", back_populates="usage_history")
    user = relationship("User", back_populates="device_history")
