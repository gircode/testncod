from datetime import datetime
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from ncod.master.core.database import Base


class HeartbeatRecord(Base):
    """心跳记录模型"""

    __tablename__ = "heartbeat_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    slave_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # online, offline, error
    last_beat_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ip_address: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    retry_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
