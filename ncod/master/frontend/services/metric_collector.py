"""Metric Collector模块"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from database import db_manager
from models.user import Device, DeviceMetric, MetricDefinition
from services.cache import cache

logger = logging.getLogger(__name__)


class MetricCollector:
    """指标收集器"""

    def __init__(self):
        self.collectors = {}  # 存储每个指标的收集任务
        self.aggregators = {}  # 存储每个指标的聚合任务

    async def start(self):
        """启动收集器"""
        try:
            with db_manager.get_session() as session:
                definitions = session.query(MetricDefinition).all()
                for definition in definitions:
                    if definition.enabled:
                        # 启动收集任务
                        collector = asyncio.create_task(
                            self._collect_metric(definition)
                        )
                        self.collectors[definition.id] = collector

                        # 如果启用了聚合,启动聚合任务
                        if definition.enable_aggregation:
                            aggregator = asyncio.create_task(
                                self._aggregate_metric(definition)
                            )
                            self.aggregators[definition.id] = aggregator
        except Exception as e:
            logger.error(f"Failed to start metric collector: {e}")

    async def stop(self):
        """停止收集器"""
        # 停止所有收集任务
        for collector in self.collectors.values():
            collector.cancel()
        self.collectors.clear()

        # 停止所有聚合任务
        for aggregator in self.aggregators.values():
            aggregator.cancel()
        self.aggregators.clear()

    async def _collect_metric(self, definition: MetricDefinition):
        """执行指标收集"""
        while True:
            try:
                # 获取所有设备
                with db_manager.get_session() as session:
                    devices = session.query(Device).all()

                    for device in devices:
                        try:
                            # 执行收集脚本
                            locals_dict = {"device": device, "definition": definition}
                            exec(definition.collection_script, globals(), locals_dict)
                            value = locals_dict.get("result")

                            if value is not None:
                                # 存储指标数据
                                metric = DeviceMetric(
                                    device_id=device.id,
                                    definition_id=definition.id,
                                    value=value,
                                    collected_at=datetime.utcnow(),
                                )
                                session.add(metric)

                                # 更新缓存
                                cache_key = f"metric:{device.id}:{definition.id}"
                                await cache.set(
                                    cache_key,
                                    {
                                        "value": value,
                                        "timestamp": datetime.utcnow().timestamp(),
                                    },
                                )

                        except Exception as e:
                            logger.error(
                                f"Failed to collect metric for device {device.id}: {e}"
                            )

                    session.commit()

            except Exception as e:
                logger.error(f"Metric collection failed: {e}")

            # 等待下一个收集间隔
            await asyncio.sleep(definition.collection_interval)

    async def _aggregate_metric(self, definition: MetricDefinition):
        """执行指标聚合"""
        while True:
            try:
                with db_manager.get_session() as session:
                    # 处理每个聚合规则
                    for agg_type, interval in definition.aggregation_rules.items():
                        # 解析时间间隔
                        if interval.endswith("m"):
                            delta = timedelta(minutes=int(interval[:-1]))
                        elif interval.endswith("h"):
                            delta = timedelta(hours=int(interval[:-1]))
                        elif interval.endswith("d"):
                            delta = timedelta(days=int(interval[:-1]))
                        else:
                            continue

                        # 获取时间范围内的数据
                        start_time = datetime.utcnow() - delta
                        metrics = (
                            session.query(DeviceMetric)
                            .filter(
                                DeviceMetric.definition_id == definition.id,
                                DeviceMetric.collected_at >= start_time,
                            )
                            .all()
                        )

                        # 按设备分组
                        device_metrics = {}
                        for metric in metrics:
                            if metric.device_id not in device_metrics:
                                device_metrics[metric.device_id] = []
                            device_metrics[metric.device_id].append(float(metric.value))

                        # 计算聚合值
                        for device_id, values in device_metrics.items():
                            if agg_type == "avg":
                                agg_value = sum(values) / len(values)
                            elif agg_type == "max":
                                agg_value = max(values)
                            elif agg_type == "min":
                                agg_value = min(values)
                            elif agg_type == "sum":
                                agg_value = sum(values)
                            else:
                                continue

                            # 存储聚合结果
                            metric = DeviceMetric(
                                device_id=device_id,
                                definition_id=definition.id,
                                value=agg_value,
                                collected_at=datetime.utcnow(),
                                is_aggregated=True,
                                aggregation_type=agg_type,
                                aggregation_interval=interval,
                            )
                            session.add(metric)

                            # 更新缓存
                            cache_key = f"metric:{device_id}:{definition.id}:{agg_type}"
                            await cache.set(
                                cache_key,
                                {
                                    "value": agg_value,
                                    "timestamp": datetime.utcnow().timestamp(),
                                },
                            )

                    session.commit()

            except Exception as e:
                logger.error(f"Metric aggregation failed: {e}")

            # 每分钟执行一次聚合
            await asyncio.sleep(60)

    async def get_metric_value(
        self, device_id: int, definition_id: int, use_cache: bool = True
    ) -> Dict[str, Any]:
        """获取指标值"""
        try:
            if use_cache:
                # 尝试从缓存获取
                cache_key = f"metric:{device_id}:{definition_id}"
                cached = await cache.get(cache_key)
                if cached:
                    return cached

            # 从数据库获取最新值
            with db_manager.get_session() as session:
                metric = (
                    session.query(DeviceMetric)
                    .filter(
                        DeviceMetric.device_id == device_id,
                        DeviceMetric.definition_id == definition_id,
                    )
                    .order_by(DeviceMetric.collected_at.desc())
                    .first()
                )

                if metric:
                    result = {
                        "value": float(metric.value),
                        "timestamp": metric.collected_at.timestamp(),
                    }

                    # 更新缓存
                    if use_cache:
                        await cache.set(cache_key, result)

                    return result

            return None

        except Exception as e:
            logger.error(f"Failed to get metric value: {e}")
            return None

    async def get_metric_history(
        self,
        device_id: int,
        definition_id: int,
        start_time: datetime,
        end_time: datetime = None,
        aggregation_type: str = None,
    ) -> List[Dict[str, Any]]:
        """获取指标历史数据"""
        try:
            if end_time is None:
                end_time = datetime.utcnow()

            with db_manager.get_session() as session:
                query = session.query(DeviceMetric).filter(
                    DeviceMetric.device_id == device_id,
                    DeviceMetric.definition_id == definition_id,
                    DeviceMetric.collected_at.between(start_time, end_time),
                )

                if aggregation_type:
                    query = query.filter(
                        DeviceMetric.is_aggregated == True,
                        DeviceMetric.aggregation_type == aggregation_type,
                    )
                else:
                    query = query.filter(DeviceMetric.is_aggregated == False)

                metrics = query.order_by(DeviceMetric.collected_at.asc()).all()

                return [
                    {"value": float(m.value), "timestamp": m.collected_at.timestamp()}
                    for m in metrics
                ]

        except Exception as e:
            logger.error(f"Failed to get metric history: {e}")
            return []


# 创建指标收集器实例
metric_collector = MetricCollector()
