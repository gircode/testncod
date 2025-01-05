"""
认证服务测试
"""

from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.user import User
from ..services.auth import AuthService
from ..services.login_history import LoginHistoryService

pytestmark = pytest.mark.asyncio


async def test_login_success(client: AsyncClient, test_user: User, db: AsyncSession):
    """测试登录成功"""
    login_data = {"username": test_user.email, "password": "testpassword123"}

    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # 验证登录历史记录
    service = LoginHistoryService(db)
    history = await service.get_user_login_history(test_user.id)
    assert history[0][0].success is True
    assert history[0][0].error_message is None


async def test_login_invalid_password(
    client: AsyncClient, test_user: User, db: AsyncSession
):
    """测试登录失败 - 密码错误"""
    login_data = {"username": test_user.email, "password": "wrongpassword"}

    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401

    # 验证登录历史记录
    service = LoginHistoryService(db)
    history = await service.get_user_login_history(test_user.id)
    assert history[0][0].success is False
    assert "Invalid credentials" in history[0][0].error_message


async def test_login_account_locked(
    client: AsyncClient, test_user: User, db: AsyncSession
):
    """测试登录失败 - 账户锁定"""
    login_data = {"username": test_user.email, "password": "wrongpassword"}

    # 尝试多次登录失败
    for _ in range(settings.MAX_LOGIN_ATTEMPTS):
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401

    # 再次尝试登录
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 403
    assert "Account is locked" in response.json()["detail"]

    # 验证登录历史记录
    service = LoginHistoryService(db)
    history = await service.get_user_login_history(test_user.id)
    assert len(history[0]) == settings.MAX_LOGIN_ATTEMPTS + 1
    assert history[0][-1].success is False
    assert "Account is locked" in history[0][-1].error_message


async def test_register_success(client: AsyncClient, db: AsyncSession):
    """测试注册成功"""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }

    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]

    # 验证登录历史记录
    service = LoginHistoryService(db)
    history = await service.get_user_login_history(data["id"])
    assert history[0][0].success is True
    assert "User registration" in history[0][0].error_message


async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    """测试注册失败 - 邮箱已存在"""
    user_data = {
        "email": test_user.email,
        "password": "testpassword123",
        "full_name": "Test User",
    }

    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


async def test_get_current_user(
    client: AsyncClient, test_user: User, normal_user_token_headers: dict
):
    """测试获取当前用户信息"""
    response = await client.get("/api/v1/auth/me", headers=normal_user_token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


async def test_update_current_user(
    client: AsyncClient, test_user: User, normal_user_token_headers: dict
):
    """测试更新当前用户信息"""
    user_data = {"full_name": "Updated Name"}

    response = await client.put(
        "/api/v1/auth/me", headers=normal_user_token_headers, json=user_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == user_data["full_name"]


async def test_delete_current_user(
    client: AsyncClient,
    test_user: User,
    normal_user_token_headers: dict,
    db: AsyncSession,
):
    """测试删除当前用户"""
    response = await client.delete("/api/v1/auth/me", headers=normal_user_token_headers)
    assert response.status_code == 204

    # 验证用户已删除
    auth_service = AuthService(db)
    user = await auth_service.get_user(test_user.id)
    assert user is None
