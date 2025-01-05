"""
会话管理模块
"""

import json
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
from uuid import uuid4

import redis.asyncio
from app.core.config import settings
from fastapi import HTTPException, Request
from starlette.datastructures import MutableHeaders
from starlette.middleware.sessions import SessionMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RedisSessionStore:
    """Redis会话存储"""

    def __init__(self):
        self.redis: Optional[redis.asyncio.Redis] = None
        self.prefix = "session:"
        self.expire = settings.SESSION_LIFETIME * 24 * 60 * 60  # 转换为秒

    async def setup(self):
        """初始化Redis连接"""
        if not self.redis:
            pool = redis.asyncio.ConnectionPool.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            self.redis = redis.asyncio.Redis(connection_pool=pool)

    async def create(self, data: Optional[Dict[str, Any]] = None) -> str:
        """创建会话"""
        await self.setup()
        session_id = str(uuid4())
        if data is None:
            data = {}
        assert self.redis is not None
        await self.redis.setex(
            f"{self.prefix}{session_id}", self.expire, json.dumps(data)
        )
        return session_id

    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        await self.setup()
        assert self.redis is not None
        data = await self.redis.get(f"{self.prefix}{session_id}")
        if data:
            return json.loads(data)
        return None

    async def update(self, session_id: str, data: Dict[str, Any]) -> None:
        """更新会话"""
        await self.setup()
        assert self.redis is not None
        await self.redis.setex(
            f"{self.prefix}{session_id}", self.expire, json.dumps(data)
        )

    async def delete(self, session_id: str) -> None:
        """删除会话"""
        await self.setup()
        assert self.redis is not None
        await self.redis.delete(f"{self.prefix}{session_id}")

    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        await self.setup()
        assert self.redis is not None
        return await self.redis.exists(f"{self.prefix}{session_id}") > 0

    async def scan_keys(self, pattern: str, count: int = 100) -> Tuple[int, List[str]]:
        """扫描键"""
        await self.setup()
        assert self.redis is not None
        cursor, keys = await self.redis.scan(cursor=0, match=pattern, count=count)
        return int(cursor), cast(List[str], keys)


class CustomSessionMiddleware:
    """自定义会话中间件"""

    def __init__(
        self,
        app: ASGIApp,
        store: RedisSessionStore,
        session_cookie: str = settings.SESSION_COOKIE_NAME,
        max_age: int = settings.SESSION_LIFETIME * 24 * 60 * 60,  # 转换为秒
        path: str = "/",
        same_site: str = settings.SESSION_COOKIE_SAMESITE,
        https_only: bool = settings.SESSION_COOKIE_SECURE,
    ):
        self.app = app
        self.store = store
        self.session_cookie = session_cookie
        self.max_age = max_age
        self.path = path
        self.security_flags = "httponly; samesite=" + same_site
        if https_only:  # 仅在HTTPS下使用
            self.security_flags += "; secure"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """处理请求"""
        if scope["type"] not in ("http", "websocket"):  # 仅处理HTTP和WebSocket请求
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        # 获取会话ID
        session_id = request.cookies.get(self.session_cookie)

        # 如果没有会话ID或会话不存在，创建新会话
        if not session_id or not await self.store.exists(session_id):
            session_id = await self.store.create()
            scope["session"] = {}
        else:
            scope["session"] = await self.store.get(session_id)

        async def send_wrapper(message: Message) -> None:
            """包装响应"""
            if message["type"] == "http.response.start":
                # 设置会话cookie
                headers = MutableHeaders(scope=message)
                header_value = (
                    f"{self.session_cookie}={session_id}; "
                    f"path={self.path}; "
                    f"max-age={self.max_age}; "
                    f"{self.security_flags}"
                )
                headers.append("Set-Cookie", header_value)
            await send(message)

        async def receive_wrapper() -> Message:
            """包装请求"""
            message = await receive()
            if message["type"] == "http.disconnect":
                # 保存会话数据
                await self.store.update(session_id, scope["session"])
            return message

        await self.app(scope, receive_wrapper, send_wrapper)


class SessionManager:
    """会话管理器"""

    def __init__(self):
        self.store = RedisSessionStore()

    async def create_session(
        self, user_id: str, user_agent: str, ip_address: str
    ) -> str:
        """创建会话"""
        session_data = {
            "user_id": user_id,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "created_at": time.time(),
            "last_activity": time.time(),
        }
        return await self.store.create(session_data)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        return await self.store.get(session_id)

    async def update_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """更新会话"""
        session = await self.store.get(session_id)
        if session:
            session.update(data)
            session["last_activity"] = time.time()
            await self.store.update(session_id, session)
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    async def delete_session(self, session_id: str) -> None:
        """删除会话"""
        await self.store.delete(session_id)

    async def validate_session(
        self, session_id: str, user_id: str, user_agent: str, ip_address: str
    ) -> bool:
        """验证会话"""
        session = await self.store.get(session_id)
        if not session:
            return False

        # 检查会话是否过期
        if (
            time.time() - session["created_at"]
            > settings.SESSION_LIFETIME * 24 * 60 * 60
        ):
            await self.store.delete(session_id)
            return False

        # 验证用户信息
        if (
            session["user_id"] != user_id
            or session["user_agent"] != user_agent
            or session["ip_address"] != ip_address
        ):
            return False

        # 更新最后活动时间
        session["last_activity"] = time.time()
        await self.store.update(session_id, session)

        return True

    async def cleanup_expired_sessions(self) -> None:
        """清理过期会话"""
        await self.store.setup()
        cursor = 0
        while True:
            cursor, keys = await self.store.scan_keys(
                pattern=f"{self.store.prefix}*", count=100
            )
            for key in keys:
                session_id = key.replace(self.store.prefix, "")
                session = await self.store.get(session_id)
                if (
                    session
                    and time.time() - session["created_at"]
                    > settings.SESSION_LIFETIME * 24 * 60 * 60
                ):
                    await self.store.delete(session_id)
            if cursor == 0:
                break
