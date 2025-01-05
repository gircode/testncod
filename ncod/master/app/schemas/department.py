"""Department模块"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    """Base department model."""

    name: str = Field(..., description="Department name")
    code: str = Field(..., description="Department code")
    description: Optional[str] = Field(None, description="Department description")


class DepartmentCreate(DepartmentBase):
    """Department creation model."""

    pass


class DepartmentUpdate(BaseModel):
    """Department update model."""

    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Department(DepartmentBase):
    """Complete department model."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentWithDetails(Department):
    """Department model with related details."""

    device_count: int = Field(0, description="Number of devices in the department")
    user_count: int = Field(0, description="Number of users in the department")

    class Config:
        from_attributes = True
