"""
自定义异常类
"""

from typing import Any, Dict, Optional


class NCODException(Exception):
    """基础异常类"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        data: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.data = data or {}
        super().__init__(self.message)


class AuthenticationError(NCODException):
    """认证错误"""

    def __init__(
        self,
        message: str = "Authentication failed",
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=401, data=data)


class AuthorizationError(NCODException):
    """授权错误"""

    def __init__(
        self, message: str = "Permission denied", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=403, data=data)


class ValidationError(NCODException):
    """验证错误"""

    def __init__(
        self, message: str = "Validation failed", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=422, data=data)


class NotFoundError(NCODException):
    """资源不存在错误"""

    def __init__(
        self, message: str = "Resource not found", data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=404, data=data)


class DeviceError(NCODException):
    """设备操作错误"""

    def __init__(
        self,
        message: str = "Device operation failed",
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=500, data=data)


class DatabaseError(NCODException):
    """数据库错误"""

    def __init__(
        self,
        message: str = "Database operation failed",
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=500, data=data)


class CacheError(NCODException):
    """缓存错误"""

    def __init__(
        self,
        message: str = "Cache operation failed",
        data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=500, data=data)
