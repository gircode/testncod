"""
认证工具模块
"""

import functools
from typing import Any, Callable, Dict, Optional, TypeVar

import httpx
import streamlit as st

from ..config import settings

F = TypeVar("F", bound=Callable[..., Any])


def require_auth(func: F) -> F:
    """认证装饰器"""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not is_authenticated():
            st.error("请先登录")
            st.stop()
        return await func(*args, **kwargs)

    return wrapper


def is_authenticated() -> bool:
    """检查是否已认证"""
    return bool(st.session_state.get("access_token"))


async def get_current_user() -> Optional[Dict[str, Any]]:
    """获取当前用户信息"""
    if not is_authenticated():
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.API_URL}/api/v1/users/me",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        st.error(f"获取用户信息失败: {e}")
        return None


def logout() -> None:
    """退出登录"""
    if "access_token" in st.session_state:
        del st.session_state.access_token
    if "user" in st.session_state:
        del st.session_state.user
