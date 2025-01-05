"""
登录历史记录测试
"""

from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import LoginHistory, User
from ..services.login_history import LoginHistoryService

pytestmark = pytest.mark.asyncio


async def test_record_login_attempt(db: AsyncSession, test_user: User):
    """测试记录登录尝试"""
    service = LoginHistoryService(db)

    # 测试成功登录
    history = await service.record_login_attempt(
        user_id=test_user.id,
        success=True,
        ip_address="127.0.0.1",
        user_agent="test-agent",
    )
    assert history.success is True
    assert history.user_id == test_user.id
    assert history.ip_address == "127.0.0.1"
    assert history.user_agent == "test-agent"
    assert history.error_message is None

    # 测试失败登录
    history = await service.record_login_attempt(
        user_id=test_user.id,
        success=False,
        ip_address="127.0.0.1",
        user_agent="test-agent",
        error_message="Invalid password",
    )
    assert history.success is False
    assert history.error_message == "Invalid password"


async def test_get_user_login_history(
    db: AsyncSession,
    test_user: User,
    client: AsyncClient,
    superuser_token_headers: dict,
):
    """测试获取用户登录历史"""
    service = LoginHistoryService(db)

    # 创建测试数据
    for i in range(5):
        await service.record_login_attempt(
            user_id=test_user.id,
            success=True,
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )

    # 测试获取历史记录
    response = await client.get(
        f"/api/v1/login-history/users/{test_user.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5
    assert data["page"] == 1


async def test_is_user_locked(db: AsyncSession, test_user: User):
    """测试用户锁定检查"""
    service = LoginHistoryService(db)

    # 创建失败登录记录
    for _ in range(5):
        await service.record_login_attempt(
            user_id=test_user.id,
            success=False,
            ip_address="127.0.0.1",
            user_agent="test-agent",
            error_message="Invalid password",
        )

    # 检查是否锁定
    is_locked = await service.is_user_locked(test_user.id)
    assert is_locked is True

    # 获取失败尝试记录
    failed_attempts = await service.get_recent_failed_attempts(test_user.id)
    assert len(failed_attempts) == 5


async def test_cleanup_old_records(db: AsyncSession, test_user: User):
    """测试清理旧记录"""
    service = LoginHistoryService(db)

    # 创建旧记录
    old_date = datetime.utcnow() - timedelta(days=31)
    for _ in range(3):
        history = await service.record_login_attempt(
            user_id=test_user.id,
            success=True,
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )
        history.created_at = old_date
        await db.commit()

    # 创建新记录
    for _ in range(2):
        await service.record_login_attempt(
            user_id=test_user.id,
            success=True,
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )

    # 清理30天前的记录
    deleted_count = await service.cleanup_old_records(days=30)
    assert deleted_count == 3

    # 验证剩余记录
    result = await db.execute(select(func.count()).select_from(LoginHistory))
    remaining_count = result.scalar()
    assert remaining_count == 2
