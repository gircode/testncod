"""User模块"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user model."""

    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    role: str = Field(..., description="User role")
    department_id: int = Field(..., description="ID of department")


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., description="Password")


class UserUpdate(BaseModel):
    """User update model."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[int] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """Complete user model."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with hashed password."""

    hashed_password: str

    class Config:
        from_attributes = True
