from datetime import datetime
from typing import Dict, List
import logging
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.total_requests = 0
        self.evictions = 0
        self.memory_usage = 0
        self.last_cleanup = None

        # 按类型统计
        self.type_hits = defaultdict(int)
        self.type_misses = defaultdict(int)

        # 性能统计
        self.access_times: List[float] = []
        self.cleanup_times: List[float] = []


class CacheMonitor:
    def __init__(self):
        self.metrics = CacheMetrics()
        self.history: List[Dict] = []
        self.history_size = 1000
        self.snapshot_interval = 300  # 5分钟

        # 启动快照任务
        asyncio.create_task(self._snapshot_loop())

    def record_hit(self, cache_type: str, access_time: float):
        """记录缓存命中"""
        self.metrics.hits += 1
        self.metrics.total_requests += 1
        self.metrics.type_hits[cache_type] += 1
        self.metrics.access_times.append(access_time)

    def record_miss(self, cache_type: str, access_time: float):
        """记录缓存未命中"""
        self.metrics.misses += 1
        self.metrics.total_requests += 1
        self.metrics.type_misses[cache_type] += 1
        self.metrics.access_times.append(access_time)

    def record_eviction(self):
        """记录缓存淘汰"""
        self.metrics.evictions += 1

    def record_cleanup(self, duration: float):
        """记录清理操作"""
        self.metrics.cleanup_times.append(duration)
        self.metrics.last_cleanup = datetime.utcnow()

    def update_memory_usage(self, usage: int):
        """更新内存使用"""
        self.metrics.memory_usage = usage

    def get_current_metrics(self) -> Dict:
        """获取当前指标"""
        total = self.metrics.total_requests
        hit_rate = (self.metrics.hits / total * 100) if total > 0 else 0

        access_times = self.metrics.access_times[-1000:]  # 最近1000次
        avg_access_time = sum(access_times) / len(access_times) if access_times else 0

        return {
            "total_requests": total,
            "hits": self.metrics.hits,
            "misses": self.metrics.misses,
            "hit_rate": round(hit_rate, 2),
            "evictions": self.metrics.evictions,
            "memory_usage": self.metrics.memory_usage,
            "avg_access_time": round(avg_access_time * 1000, 2),  # 转换为毫秒
            "last_cleanup": self.metrics.last_cleanup,
            "type_stats": {
                cache_type: {
                    "hits": self.metrics.type_hits[cache_type],
                    "misses": self.metrics.type_misses[cache_type],
                    "hit_rate": (
                        round(
                            self.metrics.type_hits[cache_type]
                            / (
                                self.metrics.type_hits[cache_type]
                                + self.metrics.type_misses[cache_type]
                            )
                            * 100,
                            2,
                        )
                        if (
                            self.metrics.type_hits[cache_type]
                            + self.metrics.type_misses[cache_type]
                        )
                        > 0
                        else 0
                    ),
                }
                for cache_type in set(self.metrics.type_hits.keys())
                | set(self.metrics.type_misses.keys())
            },
        }

    def get_history(self) -> List[Dict]:
        """获取历史指标"""
        return self.history

    async def _snapshot_loop(self):
        """定期保存指标快照"""
        while True:
            try:
                metrics = self.get_current_metrics()
                metrics["timestamp"] = datetime.utcnow()

                self.history.append(metrics)
                if len(self.history) > self.history_size:
                    self.history = self.history[-self.history_size :]

                await asyncio.sleep(self.snapshot_interval)
            except Exception as e:
                logger.error(f"Error taking metrics snapshot: {e}")
