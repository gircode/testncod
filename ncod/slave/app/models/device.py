"""
设备模型
"""

import uuid
from typing import Any, Dict

from sqlalchemy import JSON, Boolean, Column, String
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class Device(Base):
    """设备模型"""

    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    address = Column(String(200), nullable=False)
    port = Column(String(10), nullable=False)
    is_connected = Column(Boolean, default=False)
    status = Column(String(20), default="offline")
    config = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type,
            "address": self.address,
            "port": self.port,
            "is_connected": self.is_connected,
            "status": self.status,
            "config": self.config,
            "metadata": self.metadata,
        }
