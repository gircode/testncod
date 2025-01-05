"""
异常模块
"""

from typing import Any, Dict, Optional

from app.core.error_handler import BaseError
from fastapi import status


class SecurityError(BaseError):
    """安全相关错误"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            code=code or "SECURITY_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class AuthenticationError(BaseError):
    """认证错误"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            code=code or "AUTHENTICATION_ERROR",
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(BaseError):
    """授权错误"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            code=code or "AUTHORIZATION_ERROR",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ValidationError(BaseError):
    """验证错误"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            code=code or "VALIDATION_ERROR",
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class NotFoundError(BaseError):
    """未找到错误"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            code=code or "NOT_FOUND_ERROR",
            details=details,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(BaseError):
    """冲突错误"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            code=code or "CONFLICT_ERROR",
            details=details,
            status_code=status.HTTP_409_CONFLICT,
        )


class DatabaseError(BaseError):
    """数据库错误"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            code=code or "DATABASE_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
