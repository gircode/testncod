"""认证API测试"""

import pytest
from fastapi import status
from ...models.user import UserCreate


def test_register(client):
    """测试用户注册"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test@123",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login(client, db):
    """测试用户登录"""
    # 创建测试用户
    user_data = UserCreate(
        username="testuser", email="test@example.com", password="Test@123"
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"username": user_data.username, "password": user_data.password},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
