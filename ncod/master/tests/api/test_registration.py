"""
注册功能测试
"""

import pytest
from app.core.config import settings
from app.models.auth import RegistrationRequest, User
from app.services.registration import RegistrationService
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def test_request_registration(client: AsyncClient, db: AsyncSession):
    """测试注册申请"""
    response = await client.post(
        f"{settings.API_V1_STR}/registration/request",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "department_id": 1,
            "group_id": 1,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["status"] == "pending"


async def test_verify_email(client: AsyncClient, db: AsyncSession):
    """测试邮箱验证"""
    # 创建注册申请
    registration_service = RegistrationService(db)
    request = await registration_service.request_registration(
        username="testuser2",
        email="test2@example.com",
        password="testpass123",
        department_id=1,
        group_id=1,
        registration_ip="127.0.0.1",
    )

    response = await client.post(
        f"{settings.API_V1_STR}/registration/verify",
        json={"request_id": request.id, "verification_code": request.verification_code},
    )

    assert response.status_code == 200
    assert response.json() is True


async def test_approve_registration(
    client: AsyncClient, db: AsyncSession, admin_token_headers: dict
):
    """测试批准注册"""
    # 创建并验证注册申请
    registration_service = RegistrationService(db)
    request = await registration_service.request_registration(
        username="testuser3",
        email="test3@example.com",
        password="testpass123",
        department_id=1,
        group_id=1,
        registration_ip="127.0.0.1",
    )
    await registration_service.verify_email(request.id, request.verification_code)

    response = await client.post(
        f"{settings.API_V1_STR}/registration/approve",
        headers=admin_token_headers,
        json={"request_id": request.id, "is_temporary": True, "valid_days": 30},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser3"
    assert data["email"] == "test3@example.com"
    assert data["is_temporary"] is True


async def test_reject_registration(
    client: AsyncClient, db: AsyncSession, admin_token_headers: dict
):
    """测试拒绝注册"""
    # 创建注册申请
    registration_service = RegistrationService(db)
    request = await registration_service.request_registration(
        username="testuser4",
        email="test4@example.com",
        password="testpass123",
        department_id=1,
        group_id=1,
        registration_ip="127.0.0.1",
    )

    response = await client.post(
        f"{settings.API_V1_STR}/registration/reject",
        headers=admin_token_headers,
        json={"request_id": request.id, "remarks": "测试拒绝"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["remarks"] == "测试拒绝"


async def test_get_pending_requests(
    client: AsyncClient, db: AsyncSession, admin_token_headers: dict
):
    """测试获取待处理注册申请"""
    # 创建多个注册申请
    registration_service = RegistrationService(db)
    for i in range(3):
        await registration_service.request_registration(
            username=f"testuser{i+5}",
            email=f"test{i+5}@example.com",
            password="testpass123",
            department_id=1,
            group_id=1,
            registration_ip="127.0.0.1",
        )

    response = await client.get(
        f"{settings.API_V1_STR}/registration/pending", headers=admin_token_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # 可能包含其他测试创建的申请
    assert all(r["status"] == "pending" for r in data)
