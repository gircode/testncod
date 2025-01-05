"""设备模型"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from ..core.db.base import Base


class Device(Base):
    """设备数据库模型"""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    device_type = Column(String(20), nullable=False)
    serial_number = Column(String(50), unique=True, index=True)
    mac_address = Column(String(17), unique=True, index=True)
    ip_address = Column(String(15), nullable=True)
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_online = Column(DateTime, nullable=True)

    # 关系
    owner = relationship("User", back_populates="devices")
    ports = relationship("DevicePort", back_populates="device")


class DevicePort(Base):
    """设备端口模型"""

    __tablename__ = "device_ports"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    port_number = Column(Integer, nullable=False)
    port_type = Column(String(20), nullable=False)
    is_enabled = Column(Boolean, default=True)
    is_occupied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    device = relationship("Device", back_populates="ports")


# Pydantic模型
class DeviceBase(BaseModel):
    """设备基础模型"""

    name: str = Field(..., min_length=1, max_length=50)
    device_type: str = Field(..., min_length=1, max_length=20)
    serial_number: str = Field(..., min_length=1, max_length=50)
    mac_address: str = Field(..., regex=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
    ip_address: str | None = Field(None, regex=r"^(\d{1,3}\.){3}\d{1,3}$")
    is_active: bool = True


class DeviceCreate(DeviceBase):
    """设备创建模型"""

    owner_id: int


class DeviceUpdate(BaseModel):
    """设备更新模型"""

    name: str | None = None
    ip_address: str | None = None
    is_active: bool | None = None


class DeviceInDBBase(DeviceBase):
    """数据库中的设备基础模型"""

    id: int
    owner_id: int
    is_online: bool
    created_at: datetime
    updated_at: datetime
    last_online: datetime | None = None

    class Config:
        from_attributes = True


class Device(DeviceInDBBase):
    """设备API模型"""

    pass
