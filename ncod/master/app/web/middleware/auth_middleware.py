"""Auth Middleware模块"""

import re
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from ...config.auth_config import UserRole, auth_config


class AuthMiddleware:
    def __init__(self):
        self.web_paths = {"/api/monitoring", "/dashboard", "/static"}  # Web访问路径

    async def __call__(self, request: Request, call_next):
        # 静态文件不需要验证
        if request.url.path.startswith("/static"):
            return await call_next(request)

        # 登录页面不需要验证
        if request.url.path == "/" or request.url.path.startswith("/api/auth"):
            return await call_next(request)

        # 判断是否为Web访问
        is_web_access = any(
            request.url.path.startswith(path) for path in self.web_paths
        )

        if is_web_access:
            # Web访问只验证权限层级
            if not await self._verify_web_permission(request):
                return JSONResponse(status_code=403, content={"detail": "权限不足"})
        else:
            # 客户端访问需要验证MAC地址
            if not await self._verify_client_access(request):
                return JSONResponse(
                    status_code=403, content={"detail": "无效的客户端访问"}
                )

        response = await call_next(request)
        return response

    async def _verify_web_permission(self, request: Request) -> bool:
        """验证Web访问权限"""
        # 从session中获取用户权限级别
        session = request.session
        if "user_role" not in session:
            return False

        user_role = session["user_role"]
        # 使用权限配置检查访问权限
        return auth_config.has_permission(user_role, request.url.path)

    async def _verify_client_access(self, request: Request) -> bool:
        """验证客户端访问"""
        # 验证MAC地址
        mac_address = request.headers.get("X-Client-MAC")
        if not mac_address:
            return False

        # 验证MAC地址格式
        if not self._is_valid_mac(mac_address):
            return False

        # 验证MAC地址是否在白名单中
        return auth_config.is_mac_allowed(mac_address)

    def _is_valid_mac(self, mac_address: str) -> bool:
        """验证MAC地址格式"""
        mac_pattern = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
        return bool(mac_pattern.match(mac_address))

    def _check_role_permission(self, role: str, path: str) -> bool:
        """检查角色权限"""
        # TODO: 实现基于角色的权限检查逻辑
        return True  # 临时返回True，需要根据实际权限配置实现
