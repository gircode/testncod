"""
错误处理模块
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ErrorHandler:
    """错误处理器"""

    def __init__(self):
        """初始化错误处理器"""
        self.errors = []

    def handle_error(self, error: Exception) -> None:
        """处理错误

        Args:
            error: 错误对象
        """
        logger.error(f"发生错误: {str(error)}")
        self.errors.append(error)

    def get_last_error(self) -> Optional[Exception]:
        """获取最后一个错误

        Returns:
            最后一个错误对象
        """
        return self.errors[-1] if self.errors else None

    def clear_errors(self) -> None:
        """清除所有错误"""
        self.errors.clear()
