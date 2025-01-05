"""Error Handler模块"""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose.exceptions import JWTError
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class ErrorHandler:
    """错误处理器"""

    def __init__(self):
        self.error_handlers = {
            SQLAlchemyError: self._handle_database_error,
            RedisError: self._handle_redis_error,
            JWTError: self._handle_auth_error,
            ValidationError: self._handle_validation_error,
            ValueError: self._handle_value_error,
            Exception: self._handle_generic_error,
        }

    async def __call__(self, request: Request, call_next) -> Union[JSONResponse, Any]:
        """中间件入口"""
        try:
            return await call_next(request)

        except Exception as e:
            # 获取异常类型对应的处理器
            handler = self.error_handlers.get(type(e), self._handle_generic_error)
            return await handler(request, e)

    def _create_error_response(
        self, status_code: int, message: str, error_type: str, details: Dict = None
    ) -> JSONResponse:
        """创建错误响应"""
        response = {
            "error": {
                "type": error_type,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": status_code,
            }
        }

        if details:
            response["error"]["details"] = details

        return JSONResponse(status_code=status_code, content=response)

    async def _handle_database_error(
        self, request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """处理数据库错误"""
        logger.error(f"Database error: {exc}\n{traceback.format_exc()}")
        return self._create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database operation failed",
            error_type="DATABASE_ERROR",
            details={"error": str(exc)},
        )

    async def _handle_redis_error(
        self, request: Request, exc: RedisError
    ) -> JSONResponse:
        """处理Redis错误"""
        logger.error(f"Redis error: {exc}\n{traceback.format_exc()}")
        return self._create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Cache operation failed",
            error_type="CACHE_ERROR",
            details={"error": str(exc)},
        )

    async def _handle_auth_error(self, request: Request, exc: JWTError) -> JSONResponse:
        """处理认证错误"""
        logger.warning(f"Authentication error: {exc}")
        return self._create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Authentication failed",
            error_type="AUTH_ERROR",
            details={"error": str(exc)},
        )

    async def _handle_validation_error(
        self, request: Request, exc: ValidationError
    ) -> JSONResponse:
        """处理验证错误"""
        logger.warning(f"Validation error: {exc}")
        return self._create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation failed",
            error_type="VALIDATION_ERROR",
            details={"errors": exc.errors()},
        )

    async def _handle_value_error(
        self, request: Request, exc: ValueError
    ) -> JSONResponse:
        """处理值错误"""
        logger.warning(f"Value error: {exc}")
        return self._create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid value",
            error_type="VALUE_ERROR",
            details={"error": str(exc)},
        )

    async def _handle_generic_error(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """处理通用错误"""
        logger.error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
        return self._create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
            error_type="INTERNAL_ERROR",
            details={"error": str(exc)} if request.app.debug else None,
        )


# 创建错误处理器实例
error_handler = ErrorHandler()
