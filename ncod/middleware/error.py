"""错误处理中间件"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from ..core.errors.exceptions import NCODException
from ..utils.logger import logger


async def error_handler(request: Request, call_next):
    """错误处理中间件"""
    try:
        return await call_next(request)
    except NCODException as e:
        logger.error(f"业务错误: {str(e)}", exc_info=True)
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        logger.error(f"系统错误: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
