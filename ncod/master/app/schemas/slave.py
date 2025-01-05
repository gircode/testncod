"""Slave模块"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SlaveBase(BaseModel):
    """Base slave model."""

    name: str = Field(..., description="Slave server name")
    ip_address: str = Field(..., description="Slave server IP address")
    description: Optional[str] = Field(None, description="Slave server description")


class SlaveCreate(SlaveBase):
    """Slave creation model."""

    api_key: str = Field(..., description="API key for authentication")


class SlaveUpdate(BaseModel):
    """Slave update model."""

    name: Optional[str] = None
    ip_address: Optional[str] = None
    description: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None


class Slave(SlaveBase):
    """Complete slave model."""

    id: int
    api_key: str
    status: str = Field(..., description="Current slave server status")
    last_seen: datetime = Field(..., description="Last time slave server was seen")
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SlaveWithDetails(Slave):
    """Slave model with related details."""

    device_count: int = Field(0, description="Number of devices managed by the slave")
    alert_count: int = Field(0, description="Number of active alerts from the slave")

    class Config:
        from_attributes = True
