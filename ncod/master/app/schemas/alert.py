"""Alert模块"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AlertBase(BaseModel):
    """Base alert model."""

    type: str = Field(..., description="Alert type")
    message: str = Field(..., description="Alert message")
    device_id: int = Field(..., description="ID of the device")
    slave_id: int = Field(..., description="ID of the slave server")


class AlertCreate(AlertBase):
    """Alert creation model."""

    pass


class AlertUpdate(BaseModel):
    """Alert update model."""

    is_resolved: Optional[bool] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class Alert(AlertBase):
    """Complete alert model."""

    id: int
    timestamp: datetime
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]

    class Config:
        from_attributes = True


class AlertWithDetails(Alert):
    """Alert model with related details."""

    device_name: str = Field(..., description="Name of the device")
    slave_name: str = Field(..., description="Name of the slave server")

    class Config:
        from_attributes = True
