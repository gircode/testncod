"""
测试配置
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..app.core.auth import create_access_token
from ..app.core.database import Base, get_db
from ..app.models.user import User

# 测试数据库URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 创建测试引擎
engine = create_async_engine(TEST_DATABASE_URL, echo=True, future=True)

# 创建测试会话
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # 创建会话
    async with TestingSessionLocal() as session:
        yield session

    # 清理数据库
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def app(db: AsyncSession) -> FastAPI:
    """创建测试应用"""
    from ..app.main import app

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_user_token_headers(test_user: User) -> dict:
    """创建测试用户的令牌头"""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_superuser_token_headers(test_superuser: User) -> dict:
    """创建测试超级用户的令牌头"""
    access_token = create_access_token(data={"sub": test_superuser.email})
    return {"Authorization": f"Bearer {access_token}"}
