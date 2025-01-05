"""
指标采集器测试模块
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import aioredis
import pytest

from ..metrics_collector import Metric, MetricsCollector, MetricValue


@pytest.fixture
def mock_redis():
    """模拟Redis客户端"""
    with patch("aioredis.from_url") as mock:
        redis = AsyncMock()
        mock.return_value = redis
        yield redis


@pytest.fixture
async def metrics_collector(mock_redis):
    """创建指标采集器"""
    collector = MetricsCollector(redis_url="redis://localhost")
    yield collector
    await collector.stop()


@pytest.mark.asyncio
async def test_start_stop(metrics_collector, mock_redis):
    """测试启动和停止"""
    # 测试启动
    await metrics_collector.start()
    assert metrics_collector.redis is not None

    # 测试停止
    await metrics_collector.stop()
    mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_add_metric(metrics_collector):
    """测试添加指标"""
    metrics_collector.add_metric(
        name="test_metric", type="gauge", description="Test metric", unit="count"
    )

    assert "test_metric" in metrics_collector.metrics
    metric = metrics_collector.metrics["test_metric"]
    assert metric.name == "test_metric"
    assert metric.type == "gauge"
    assert metric.description == "Test metric"
    assert metric.unit == "count"
    assert metric.values == []


@pytest.mark.asyncio
async def test_record_metric(metrics_collector, mock_redis):
    """测试记录指标值"""
    # 添加测试指标
    metrics_collector.add_metric(
        name="test_metric", type="gauge", description="Test metric", unit="count"
    )

    # 记录指标值
    await metrics_collector.record_metric(
        name="test_metric", value=42.0, labels={"host": "test"}
    )

    # 验证内存中的指标值
    metric = metrics_collector.metrics["test_metric"]
    assert len(metric.values) == 1
    assert metric.values[0].value == 42.0
    assert metric.values[0].labels == {"host": "test"}

    # 验证Redis存储
    mock_redis.lpush.assert_called_once()
    mock_redis.ltrim.assert_called_once()

    # 测试记录不存在的指标
    await metrics_collector.record_metric(name="nonexistent", value=42.0)
    # 应该只有一次lpush调用
    assert mock_redis.lpush.call_count == 1


@pytest.mark.asyncio
async def test_get_metric_values(metrics_collector):
    """测试获取指标值"""
    # 添加测试指标
    metrics_collector.add_metric(
        name="test_metric", type="gauge", description="Test metric", unit="count"
    )

    # 添加测试数据
    now = datetime.now()
    test_values = [
        MetricValue(value=1.0, timestamp=now - timedelta(minutes=2)),
        MetricValue(value=2.0, timestamp=now - timedelta(minutes=1)),
        MetricValue(value=3.0, timestamp=now),
    ]
    metrics_collector.metrics["test_metric"].values = test_values

    # 测试获取所有值
    values = await metrics_collector.get_metric_values("test_metric")
    assert len(values) == 3
    assert values == test_values

    # 测试时间范围过滤
    values = await metrics_collector.get_metric_values(
        "test_metric",
        start_time=now - timedelta(minutes=1.5),
        end_time=now - timedelta(seconds=30),
    )
    assert len(values) == 1
    assert values[0].value == 2.0

    # 测试不存在的指标
    values = await metrics_collector.get_metric_values("nonexistent")
    assert values == []


@pytest.mark.asyncio
async def test_export_metrics(metrics_collector):
    """测试导出指标"""
    # 添加测试指标
    metrics_collector.add_metric(
        name="test_gauge", type="gauge", description="Test gauge metric", unit="count"
    )
    metrics_collector.add_metric(
        name="test_counter",
        type="counter",
        description="Test counter metric",
        unit="bytes",
    )

    # 添加测试数据
    now = datetime.now()
    metrics_collector.metrics["test_gauge"].values = [
        MetricValue(value=42.0, timestamp=now, labels={"host": "test"})
    ]
    metrics_collector.metrics["test_counter"].values = [
        MetricValue(value=1000, timestamp=now, labels={"direction": "in"})
    ]

    # 导出指标
    exported = await metrics_collector.export_metrics()

    assert "test_gauge" in exported
    assert exported["test_gauge"]["type"] == "gauge"
    assert exported["test_gauge"]["unit"] == "count"
    assert len(exported["test_gauge"]["values"]) == 1
    assert exported["test_gauge"]["values"][0]["value"] == 42.0

    assert "test_counter" in exported
    assert exported["test_counter"]["type"] == "counter"
    assert exported["test_counter"]["unit"] == "bytes"
    assert len(exported["test_counter"]["values"]) == 1
    assert exported["test_counter"]["values"][0]["value"] == 1000


@pytest.mark.asyncio
async def test_import_metrics(metrics_collector):
    """测试导入指标"""
    # 准备测试数据
    now = datetime.now()
    import_data = {
        "test_metric": {
            "type": "gauge",
            "description": "Test metric",
            "unit": "count",
            "values": [
                {
                    "value": 42.0,
                    "timestamp": now.isoformat(),
                    "labels": {"host": "test"},
                }
            ],
        }
    }

    # 导入指标
    await metrics_collector.import_metrics(import_data)

    assert "test_metric" in metrics_collector.metrics
    metric = metrics_collector.metrics["test_metric"]
    assert metric.type == "gauge"
    assert metric.description == "Test metric"
    assert metric.unit == "count"
    assert len(metric.values) == 1
    assert metric.values[0].value == 42.0
    assert metric.values[0].labels == {"host": "test"}


@pytest.mark.asyncio
async def test_clear_metrics(metrics_collector):
    """测试清除指标"""
    # 添加测试指标
    metrics_collector.add_metric(
        name="metric1", type="gauge", description="Test metric 1"
    )
    metrics_collector.add_metric(
        name="metric2", type="gauge", description="Test metric 2"
    )

    # 添加测试数据
    now = datetime.now()
    metrics_collector.metrics["metric1"].values = [
        MetricValue(value=1.0, timestamp=now)
    ]
    metrics_collector.metrics["metric2"].values = [
        MetricValue(value=2.0, timestamp=now)
    ]

    # 清除单个指标
    metrics_collector.clear_metrics("metric1")
    assert len(metrics_collector.metrics["metric1"].values) == 0
    assert len(metrics_collector.metrics["metric2"].values) == 1

    # 清除所有指标
    metrics_collector.clear_metrics()
    assert len(metrics_collector.metrics["metric1"].values) == 0
    assert len(metrics_collector.metrics["metric2"].values) == 0


@pytest.mark.asyncio
async def test_calculate_statistics(metrics_collector):
    """测试计算统计信息"""
    # 添加测试指标
    metrics_collector.add_metric(
        name="test_metric", type="gauge", description="Test metric"
    )

    # 添加测试数据
    now = datetime.now()
    metrics_collector.metrics["test_metric"].values = [
        MetricValue(value=1.0, timestamp=now),
        MetricValue(value=2.0, timestamp=now),
        MetricValue(value=3.0, timestamp=now),
        MetricValue(value=4.0, timestamp=now),
        MetricValue(value=5.0, timestamp=now),
    ]

    # 计算统计信息
    stats = await metrics_collector.calculate_statistics("test_metric")
    assert stats["count"] == 5
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["avg"] == 3.0
    assert stats["last"] == 5.0

    # 测试空指标
    stats = await metrics_collector.calculate_statistics("nonexistent")
    assert stats == {}


@pytest.mark.asyncio
async def test_redis_integration(metrics_collector, mock_redis):
    """测试Redis集成"""
    # 添加测试指标
    metrics_collector.add_metric(
        name="test_metric", type="gauge", description="Test metric"
    )

    # 记录指标值
    await metrics_collector.record_metric(
        name="test_metric", value=42.0, labels={"host": "test"}
    )

    # 验证Redis操作
    assert mock_redis.lpush.called
    assert mock_redis.ltrim.called

    # 模拟Redis错误
    mock_redis.lpush.side_effect = aioredis.RedisError
    await metrics_collector.record_metric(name="test_metric", value=43.0)
    # 应该继续工作，但会记录错误
