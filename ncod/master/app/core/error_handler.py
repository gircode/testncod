"""
错误处理模块
"""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class BaseError(Exception):
    """基础错误类"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


class ErrorHandler:
    """错误处理器"""

    def __init__(self):
        self.logger = logger

    def handle_error(self, error: BaseError):
        """处理错误

        Args:
            error: 错误对象
        """
        # 记录错误日志
        self.logger.error(
            f"Error occurred: {error.message}",
            extra={
                "code": error.code,
                "details": error.details,
                "status_code": error.status_code,
            },
        )

        # 转换为HTTP异常
        raise HTTPException(
            status_code=error.status_code,
            detail={
                "message": error.message,
                "code": error.code,
                "details": error.details,
            },
        )

    def handle_database_error(self, error: Exception):
        """处理数据库错误

        Args:
            error: 数据库错误
        """
        self.logger.error(f"Database error occurred: {str(error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="数据库操作失败"
        )

    def handle_validation_error(self, error: Exception):
        """处理验证错误

        Args:
            error: 验证错误
        """
        self.logger.warning(f"Validation error occurred: {str(error)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        )

    def handle_authentication_error(self, error: Exception):
        """处理认证错误

        Args:
            error: 认证错误
        """
        self.logger.warning(
            f"Authentication error occurred: {str(error)}", exc_info=True
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error))

    def handle_authorization_error(self, error: Exception):
        """处理授权错误

        Args:
            error: 授权错误
        """
        self.logger.warning(
            f"Authorization error occurred: {str(error)}", exc_info=True
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))

    def handle_not_found_error(self, error: Exception):
        """处理未找到错误

        Args:
            error: 未找到错误
        """
        self.logger.warning(f"Not found error occurred: {str(error)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))

    def handle_conflict_error(self, error: Exception):
        """处理冲突错误

        Args:
            error: 冲突错误
        """
        self.logger.warning(f"Conflict error occurred: {str(error)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
