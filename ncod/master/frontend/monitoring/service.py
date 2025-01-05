"""
Monitoring Service Module
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import psutil
from prometheus_client import start_http_server

from .collector import MetricsCollector
from .config import MonitoringConfig
from .metrics import (
    CACHE_SIZE,
    DB_CONNECTION_POOL,
    NODE_STATUS,
    SYSTEM_CPU,
    SYSTEM_MEMORY,
)

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for managing monitoring system"""

    def __init__(self, config: MonitoringConfig):
        """Initialize monitoring service"""
        self.config = config
        self.collector = MetricsCollector()
        self._running = False
        self._tasks = []

    async def start(self):
        """Start monitoring service"""
        if self._running:
            return

        self._running = True

        # Start Prometheus HTTP server
        try:
            start_http_server(port=self.config.prometheus_port, addr="0.0.0.0")
            logger.info(
                f"Started Prometheus metrics server on port \
                     {self.config.prometheus_port}"
            )
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
            raise

        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._collect_system_metrics()),
            asyncio.create_task(self._check_node_health()),
            asyncio.create_task(self._collect_db_stats()),
            asyncio.create_task(self._collect_cache_stats()),
            asyncio.create_task(self._export_metrics()),
        ]

        logger.info("Monitoring service started")

    async def stop(self):
        """Stop monitoring service"""
        if not self._running:
            return

        self._running = False

        # Cancel all background tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []

        logger.info("Monitoring service stopped")

    async def _collect_system_metrics(self):
        """Collect system metrics periodically"""
        while self._running:
            try:
                # CPU metrics
                cpu_times = psutil.cpu_times_percent()
                SYSTEM_CPU.labels(type="user").set(cpu_times.user)
                SYSTEM_CPU.labels(type="system").set(cpu_times.system)
                SYSTEM_CPU.labels(type="idle").set(cpu_times.idle)

                # Memory metrics
                memory = psutil.virtual_memory()
                SYSTEM_MEMORY.labels(type="total").set(memory.total)
                SYSTEM_MEMORY.labels(type="available").set(memory.available)
                SYSTEM_MEMORY.labels(type="used").set(memory.used)
                SYSTEM_MEMORY.labels(type="free").set(memory.free)

                # Process metrics
                process = psutil.Process(os.getpid())
                SYSTEM_MEMORY.labels(type="process_rss").set(process.memory_info().rss)
                SYSTEM_MEMORY.labels(type="process_vms").set(process.memory_info().vms)
                SYSTEM_CPU.labels(type="process").set(process.cpu_percent())

                # Check thresholds and log warnings
                self._check_resource_thresholds(cpu_times, memory)

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")

            await asyncio.sleep(self.config.collection_interval)

    def _check_resource_thresholds(self, cpu_times, memory):
        """Check resource usage against thresholds"""
        # CPU usage warning
        cpu_usage = 100 - cpu_times.idle
        if cpu_usage > self.config.cpu_usage_threshold:
            logger.warning(
                f"CPU usage ({cpu_usage:.1f}%) exceeds threshold "
                f"({self.config.cpu_usage_threshold}%)"
            )

        # Memory usage warning
        memory_usage = (memory.total - memory.available) / memory.total * 100
        if memory_usage > self.config.memory_usage_threshold:
            logger.warning(
                f"Memory usage ({memory_usage:.1f}%) exceeds threshold "
                f"({self.config.memory_usage_threshold}%)"
            )

        # Disk usage warning
        disk = psutil.disk_usage("/")
        disk_usage = disk.percent
        if disk_usage > self.config.disk_usage_threshold:
            logger.warning(
                f"Disk usage ({disk_usage:.1f}%) exceeds threshold "
                f"({self.config.disk_usage_threshold}%)"
            )

    async def _check_node_health(self):
        """Check health of nodes periodically"""
        while self._running:
            try:
                # Get list of nodes from cluster manager
                nodes = await self._get_cluster_nodes()

                for node in nodes:
                    try:
                        # Check node health
                        is_healthy = await self._check_node(
                            node, timeout=self.config.node_health_check_timeout
                        )

                        # Update node status metric
                        NODE_STATUS.labels(node_id=node["id"], role=node["role"]).set(
                            1 if is_healthy else 0
                        )

                        if not is_healthy:
                            logger.warning(f"Node {node['id']} is unhealthy")

                    except Exception as e:
                        logger.error(f"Error checking node {node['id']}: {e}")
                        NODE_STATUS.labels(node_id=node["id"], role=node["role"]).set(0)

            except Exception as e:
                logger.error(f"Error in node health check: {e}")

            await asyncio.sleep(self.config.node_health_check_interval)

    async def _collect_db_stats(self):
        """Collect database statistics periodically"""
        while self._running:
            try:
                # Get database connection pool stats
                pool_stats = await self._get_db_pool_stats()

                for status, count in pool_stats.items():
                    DB_CONNECTION_POOL.labels(status=status).set(count)

                # Log slow queries if enabled
                if self.config.db_slow_query_threshold > 0:
                    await self._check_slow_queries()

            except Exception as e:
                logger.error(f"Error collecting database stats: {e}")

            await asyncio.sleep(self.config.collection_interval)

    async def _collect_cache_stats(self):
        """Collect cache statistics periodically"""
        while self._running:
            try:
                # Get cache stats for each cache instance
                cache_stats = await self._get_cache_stats()

                for cache_name, stats in cache_stats.items():
                    CACHE_SIZE.labels(cache=cache_name).set(stats["size"])

            except Exception as e:
                logger.error(f"Error collecting cache stats: {e}")

            await asyncio.sleep(self.config.cache_stats_interval)

    async def _export_metrics(self):
        """Export metrics periodically"""
        if not self.config.export_metrics:
            return

        while self._running:
            try:
                # Export metrics based on configuration
                if self.config.export_format == "prometheus":
                    if self.config.prometheus_pushgateway:
                        await self._export_to_pushgateway()
                else:
                    await self._export_to_file()

            except Exception as e:
                logger.error(f"Error exporting metrics: {e}")

            await asyncio.sleep(self.config.export_interval)

    async def _get_cluster_nodes(self) -> list:
        """Get list of cluster nodes"""
        # TODO: Implement actual cluster node discovery
        return [{"id": "node1", "role": "master"}, {"id": "node2", "role": "slave"}]

    async def _check_node(self, node: Dict[str, Any], timeout: float) -> bool:
        """Check health of a single node"""
        # TODO: Implement actual node health check
        return True

    async def _get_db_pool_stats(self) -> Dict[str, int]:
        """Get database connection pool statistics"""
        # TODO: Implement actual database pool stats collection
        return {"active": 5, "idle": 3, "total": 8}

    async def _check_slow_queries(self):
        """Check and log slow queries"""
        # TODO: Implement slow query detection
        pass

    async def _get_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get cache statistics"""
        # TODO: Implement actual cache stats collection
        return {"main": {"size": 1000}, "session": {"size": 500}}

    async def _export_to_pushgateway(self):
        """Export metrics to Prometheus Pushgateway"""
        # TODO: Implement Pushgateway export
        pass

    async def _export_to_file(self):
        """Export metrics to file"""
        # TODO: Implement file export
        pass
