"""
密码相关的数据模式
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator

from ..core.config import settings


class PasswordReset(BaseModel):
    """密码重置请求"""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """密码重置确认"""

    token: str
    new_password: str = Field(
        ...,
        min_length=settings.PASSWORD_MIN_LENGTH,
        max_length=settings.PASSWORD_MAX_LENGTH,
    )

    @validator("new_password")
    def validate_password(cls, v):
        """验证密码强度"""
        if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if settings.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if settings.PASSWORD_REQUIRE_SPECIAL and not any(not c.isalnum() for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class PasswordChange(BaseModel):
    """密码修改"""

    current_password: str
    new_password: str = Field(
        ...,
        min_length=settings.PASSWORD_MIN_LENGTH,
        max_length=settings.PASSWORD_MAX_LENGTH,
    )

    @validator("new_password")
    def validate_password(cls, v):
        """验证密码强度"""
        if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if settings.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if settings.PASSWORD_REQUIRE_SPECIAL and not any(not c.isalnum() for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    @validator("new_password")
    def validate_different_password(cls, v, values):
        """验证新密码与当前密码不同"""
        if "current_password" in values and v == values["current_password"]:
            raise ValueError("New password must be different from current password")
        return v
