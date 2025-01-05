"""
同步模型
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class SyncRecord(Base):
    """同步记录模型"""

    __tablename__ = "sync_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"))
    sync_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    error_message = Column(String(1000), nullable=True)
    metadata = Column(JSON, nullable=True)

    # 关联
    device = relationship("Device", back_populates="sync_records")
    items = relationship(
        "SyncItem", back_populates="record", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "device_id": str(self.device_id),
            "sync_type": self.sync_type,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "failed_items": self.failed_items,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class SyncItem(Base):
    """同步项目模型"""

    __tablename__ = "sync_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("sync_records.id"))
    item_type = Column(String(50), nullable=False)
    item_id = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")
    timestamp = Column(DateTime, default=datetime.utcnow)
    error_message = Column(String(1000), nullable=True)
    metadata = Column(JSON, nullable=True)

    # 关联
    record = relationship("SyncRecord", back_populates="items")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "record_id": str(self.record_id),
            "item_type": self.item_type,
            "item_id": self.item_id,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
            "metadata": self.metadata,
        }
