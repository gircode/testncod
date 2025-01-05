"""
测试配置
"""

import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Generator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..core.config import settings
from ..core.database import Base, get_db
from ..core.security import create_access_token, get_password_hash
from ..models.user import User
from ..services.auth import AuthService

# 测试数据库URL
TEST_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    """创建数据库引擎"""
    engine = create_async_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest.fixture
async def client(app: FastAPI, db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""

    async def _get_test_db():
        yield db

    app.dependency_overrides[get_db] = _get_test_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """创建测试用户"""
    auth_service = AuthService(db)
    user = await auth_service.create_user(
        {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        }
    )
    return user


@pytest.fixture
async def test_superuser(db: AsyncSession) -> User:
    """创建测试超级用户"""
    auth_service = AuthService(db)
    user = await auth_service.create_user(
        {
            "email": "admin@example.com",
            "password": "adminpassword123",
            "full_name": "Admin User",
            "is_superuser": True,
        }
    )
    return user


@pytest.fixture
def normal_user_token_headers(test_user: User) -> Dict[str, str]:
    """创建普通用户的认证头"""
    access_token = create_access_token(
        data={"sub": str(test_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def superuser_token_headers(test_superuser: User) -> Dict[str, str]:
    """创建超级用户的认证头"""
    access_token = create_access_token(
        data={"sub": str(test_superuser.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"Authorization": f"Bearer {access_token}"}
