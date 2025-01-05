from typing import Dict, Any


class NCODException(Exception):
    """基础异常类"""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: Dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code
        self.details = details if details is not None else {}
        super().__init__(message)


class AuthenticationError(NCODException):
    """认证相关异常"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message, code="AUTH_ERROR", details=details)


class ValidationError(NCODException):
    """数据验证异常"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class DeviceError(NCODException):
    """设备相关异常"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message, code="DEVICE_ERROR", details=details)


class DatabaseError(NCODException):
    """数据库操作异常"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message, code="DB_ERROR", details=details)


class ConfigurationError(NCODException):
    """配置相关异常"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message, code="CONFIG_ERROR", details=details)


class NetworkError(NCODException):
    """网络通信异常"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message, code="NETWORK_ERROR", details=details)


class PermissionError(NCODException):
    """权限相关异常"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message, code="PERMISSION_ERROR", details=details)


class ResourceNotFoundError(NCODException):
    """资源未找到异常"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message, code="NOT_FOUND", details=details)


class DuplicateResourceError(NCODException):
    """资源重复异常"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message, code="DUPLICATE_RESOURCE", details=details)


class ServiceUnavailableError(NCODException):
    """服务不可用异常"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message, code="SERVICE_UNAVAILABLE", details=details)


def format_error_response(error: NCODException) -> Dict[str, Any]:
    """格式化错误响应"""
    return {
        "success": False,
        "error": {
            "code": error.code,
            "message": error.message,
            "details": error.details,
        },
    }
