from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from ncod.core.db.database import Base


class DeviceUsageStats(Base):
    __tablename__ = "device_usage_stats"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    # 使用时间统计
    total_usage_time = Column(Float, default=0.0)  # 总使用时长(小时)
    daily_usage_time = Column(Float, default=0.0)  # 日使用时长
    weekly_usage_time = Column(Float, default=0.0)  # 周使用时长
    monthly_usage_time = Column(Float, default=0.0)  # 月使用时长

    # 连接统计
    connection_count = Column(Integer, default=0)  # 连接次数
    failed_connection_count = Column(Integer, default=0)  # 失败次数

    # 时间戳
    last_connected = Column(DateTime)
    last_disconnected = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    device = relationship("Device", back_populates="usage_stats")
    user = relationship("User", back_populates="device_stats")
    organization = relationship("Organization", back_populates="device_stats")


class DeviceUsageLog(Base):
    __tablename__ = "device_usage_logs"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    action = Column(String)  # connect, disconnect, error
    status = Column(String)  # success, failed
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    device = relationship("Device", back_populates="usage_logs")
    user = relationship("User", back_populates="device_logs")
    organization = relationship("Organization", back_populates="device_logs")
