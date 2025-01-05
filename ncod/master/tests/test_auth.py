"""
认证相关的测试用例
"""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ..app.core.auth import get_password_hash
from ..app.models.user import Permission, Role, User
from ..app.schemas.auth import RoleCreate, UserCreate


@pytest.fixture
def app() -> FastAPI:
    """创建测试应用"""
    from ..app.main import app

    return app


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """创建测试用户"""
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("Test123!"),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_superuser(db: AsyncSession) -> User:
    """创建测试超级用户"""
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("Admin123!"),
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_role(db: AsyncSession) -> Role:
    """创建测试角色"""
    role = Role(name="test_role", description="Test Role")
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


@pytest.fixture
async def test_permission(db: AsyncSession) -> Permission:
    """创建测试权限"""
    permission = Permission(name="test_permission", description="Test Permission")
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return role


async def test_login(client: AsyncClient, test_user: User):
    """测试用户登录"""
    response = await client.post(
        "/api/v1/auth/login", data={"username": test_user.email, "password": "Test123!"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, test_user: User):
    """测试错误密码登录"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "wrong_password"},
    )
    assert response.status_code == 401


async def test_register(client: AsyncClient, db: AsyncSession):
    """测试用户注册"""
    user_data = {
        "email": "new@example.com",
        "full_name": "New User",
        "password": "NewUser123!",
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    assert response.json()["email"] == user_data["email"]
    assert response.json()["full_name"] == user_data["full_name"]


async def test_register_existing_email(client: AsyncClient, test_user: User):
    """测试使用已存在邮箱注册"""
    user_data = {
        "email": test_user.email,
        "full_name": "Another User",
        "password": "Another123!",
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400


async def test_get_current_user(
    client: AsyncClient, test_user: User, test_user_token_headers: dict
):
    """测试获取当前用户信息"""
    response = await client.get("/api/v1/auth/me", headers=test_user_token_headers)
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email
    assert response.json()["full_name"] == test_user.full_name


async def test_update_current_user(
    client: AsyncClient, test_user: User, test_user_token_headers: dict
):
    """测试更新当前用户信息"""
    update_data = {"full_name": "Updated Name"}
    response = await client.put(
        "/api/v1/auth/me", headers=test_user_token_headers, json=update_data
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == update_data["full_name"]


async def test_list_users(
    client: AsyncClient, test_superuser: User, test_superuser_token_headers: dict
):
    """测试获取用户列表"""
    response = await client.get(
        "/api/v1/auth/users", headers=test_superuser_token_headers
    )
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()
    assert "page" in response.json()
    assert "pages" in response.json()


async def test_create_user(
    client: AsyncClient, test_superuser: User, test_superuser_token_headers: dict
):
    """测试创建用户"""
    user_data = {
        "email": "created@example.com",
        "full_name": "Created User",
        "password": "Created123!",
    }
    response = await client.post(
        "/api/v1/auth/users", headers=test_superuser_token_headers, json=user_data
    )
    assert response.status_code == 200
    assert response.json()["email"] == user_data["email"]
    assert response.json()["full_name"] == user_data["full_name"]


async def test_create_role(
    client: AsyncClient, test_superuser: User, test_superuser_token_headers: dict
):
    """测试创建角色"""
    role_data = {"name": "new_role", "description": "New Role"}
    response = await client.post(
        "/api/v1/auth/roles", headers=test_superuser_token_headers, json=role_data
    )
    assert response.status_code == 200
    assert response.json()["name"] == role_data["name"]
    assert response.json()["description"] == role_data["description"]


async def test_assign_role_to_user(
    client: AsyncClient,
    test_superuser: User,
    test_user: User,
    test_role: Role,
    test_superuser_token_headers: dict,
):
    """测试为用户分配角色"""
    response = await client.post(
        f"/api/v1/auth/users/{test_user.id}/roles/{test_role.id}",
        headers=test_superuser_token_headers,
    )
    assert response.status_code == 204


async def test_remove_role_from_user(
    client: AsyncClient,
    test_superuser: User,
    test_user: User,
    test_role: Role,
    test_superuser_token_headers: dict,
):
    """测试移除用户的角色"""
    # 先分配角色
    await client.post(
        f"/api/v1/auth/users/{test_user.id}/roles/{test_role.id}",
        headers=test_superuser_token_headers,
    )
    # 再移除角色
    response = await client.delete(
        f"/api/v1/auth/users/{test_user.id}/roles/{test_role.id}",
        headers=test_superuser_token_headers,
    )
    assert response.status_code == 204
