"""
监控服务测试
"""

import asyncio
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ..app.models.monitor import MonitorAlert, MonitorMetric
from ..app.services.health import HealthService
from ..app.services.monitor import MonitorService


@pytest.mark.asyncio
async def test_monitor_service(db_session: AsyncSession):
    """测试监控服务"""
    # 初始化服务
    monitor_service = MonitorService(db_session)

    # 测试启动和停止
    await monitor_service.start()
    assert monitor_service._running is True
    await asyncio.sleep(2)  # 等待收集一些数据
    await monitor_service.stop()
    assert monitor_service._running is False

    # 测试指标收集
    result = await db_session.execute(select(func.count()).select_from(MonitorMetric))
    count = result.scalar()
    assert count > 0

    # 测试告警创建
    await monitor_service._create_alert(
        alert_type="test",
        severity="warning",
        message="Test alert",
        metadata={"test": True},
    )

    alerts = await monitor_service.get_active_alerts()
    assert len(alerts) > 0

    # 测试告警解决
    alert_id = alerts[0]["id"]
    success = await monitor_service.resolve_alert(alert_id)
    assert success is True


@pytest.mark.asyncio
async def test_health_service(db_session: AsyncSession):
    """测试健康检查服务"""
    health_service = HealthService(db_session)

    # 测试健康检查
    status = await health_service.check()
    assert status["status"] in ["healthy", "unhealthy"]
    assert "checks" in status

    # 测试系统概况
    summary = await health_service.get_system_summary()
    assert "system" in summary
    assert "alerts" in summary
