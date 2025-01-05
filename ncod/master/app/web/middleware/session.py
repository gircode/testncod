"""Session模块"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware


class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, session_timeout: int = 30):  # 会话超时时间（分钟）
        super().__init__(app)
        self.session_timeout = session_timeout

    async def dispatch(self, request: Request, call_next) -> Response:
        # 检查会话是否过期
        session = request.session
        last_activity = session.get("last_activity")

        if last_activity:
            last_activity = datetime.fromisoformat(last_activity)
            if datetime.utcnow() - last_activity > timedelta(
                minutes=self.session_timeout
            ):
                # 会话过期，清除会话
                session.clear()

        # 更新最后活动时间
        session["last_activity"] = datetime.utcnow().isoformat()

        response = await call_next(request)
        return response


class CustomSessionMiddleware(SessionMiddleware):
    def __init__(
        self,
        app,
        secret_key: str,
        session_cookie: str = "session",
        same_site: str = "lax",
        https_only: bool = False,
    ):
        super().__init__(
            app,
            secret_key=secret_key,
            session_cookie=session_cookie,
            same_site=same_site,
            https_only=https_only,
            max_age=None,  # 使用自定义的超时机制
        )
