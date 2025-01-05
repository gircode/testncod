"""安全模块测试"""

import pytest
from jose import jwt
from ...core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    validate_password,
)
from ...config.settings import Settings

settings = Settings()


def test_password_hash():
    """测试密码哈希"""
    password = "test_password"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_password_validation():
    """测试密码验证"""
    # 有效密码
    assert validate_password("Test@123456")

    # 无效密码
    assert not validate_password("test")  # 太短
    assert not validate_password("test123456")  # 无大写字母
    assert not validate_password("TEST123456")  # 无小写字母
    assert not validate_password("Testpassword")  # 无数字
    assert not validate_password("Test123")  # 无特殊字符


def test_access_token():
    """测试访问令牌"""
    data = {"sub": "test"}
    token = create_access_token(data)
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    assert payload["sub"] == "test"
