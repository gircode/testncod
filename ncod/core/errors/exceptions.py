"""自定义异常"""

from fastapi import status


class NCODException(Exception):
    """基础异常类"""

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class AuthenticationError(NCODException):
    """认证错误"""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail, status_code=status.HTTP_401_UNAUTHORIZED)


class PermissionDenied(NCODException):
    """权限错误"""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(detail, status_code=status.HTTP_403_FORBIDDEN)


class ValidationError(NCODException):
    """验证错误"""

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(detail, status_code=status.HTTP_400_BAD_REQUEST)


class ResourceNotFound(NCODException):
    """资源不存在"""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail, status_code=status.HTTP_404_NOT_FOUND)


class ResourceConflict(NCODException):
    """资源冲突"""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail, status_code=status.HTTP_409_CONFLICT)
