"""队列相关模型"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ncod.core.db.base import Base


class PortQueue(Base):
    """端口队列模型"""

    __tablename__ = "port_queues"

    id = Column(Integer, primary_key=True, index=True)
    port_id = Column(Integer, ForeignKey("usb_ports.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="waiting")  # waiting/using/completed/cancelled
    request_time = Column(DateTime, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    estimated_duration = Column(Integer)  # 预计使用时长(分钟)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    port = relationship("USBPort", back_populates="queue")
    user = relationship("User", back_populates="port_queues")
