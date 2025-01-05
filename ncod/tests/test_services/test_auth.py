"""认证服务测试"""

import pytest
from ...services.auth import AuthService
from ...models.user import UserCreate
from ...core.errors.exceptions import ValidationError


def test_create_user(db):
    """测试创建用户"""
    auth_service = AuthService()
    user_data = UserCreate(
        username="testuser", email="test@example.com", password="Test@123"
    )
    user = auth_service.create_user(db, user_data)
    assert user.username == user_data.username
    assert user.email == user_data.email

    # 测试重复用户名
    with pytest.raises(ValidationError):
        auth_service.create_user(db, user_data)


def test_authenticate_user(db):
    """测试用户认证"""
    auth_service = AuthService()
    user_data = UserCreate(
        username="testuser", email="test@example.com", password="Test@123"
    )
    auth_service.create_user(db, user_data)

    # 正确认证
    user = auth_service.authenticate_user(db, user_data.username, user_data.password)
    assert user is not None
    assert user.username == user_data.username

    # 错误密码
    user = auth_service.authenticate_user(db, user_data.username, "wrong_password")
    assert user is None
