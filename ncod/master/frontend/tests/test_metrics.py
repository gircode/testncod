"""Test Metrics模块"""

from typing import Any, AsyncGenerator, Dict

import pytest

from ..types.fixtures import FixtureResult


@pytest.mark.asyncio
async def test_system_metrics(
    test_cpu_usage: FixtureResult[float], test_memory_usage: FixtureResult[float]
) -> None:
    """测试系统指标"""
    cpu = await anext(test_cpu_usage)
    memory = await anext(test_memory_usage)

    assert 0 <= cpu <= 100
    assert 0 <= memory <= 100


@pytest.mark.asyncio
async def test_system_status(test_status: FixtureResult[Dict[str, Any]]) -> None:
    """测试系统状态"""
    status = await anext(test_status)

    assert status["status"] in ["running", "stopped"]
    assert isinstance(status["uptime"], int)
    assert isinstance(status["connections"], int)
