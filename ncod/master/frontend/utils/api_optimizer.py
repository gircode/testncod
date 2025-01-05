"""Api Optimizer模块"""

import asyncio
import zlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import orjson
import snappy
from cachetools import TTLCache
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from .performance import cache_manager, performance_monitor


class APIResponseOptimizer:
    """API响应优化器"""

    def __init__(self):
        self.response_cache = TTLCache(maxsize=1000, ttl=300)  # 5分钟缓存
        self.compression_threshold = 1024  # 1KB
        self.compression_methods = {
            "gzip": self._compress_gzip,
            "snappy": self._compress_snappy,
        }

    async def optimize_response(
        self, data: Any, request: Request = None, compression: str = "gzip"
    ) -> Response:
        """优化API响应"""
        start_time = datetime.now()

        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(data, request)

            # 检查缓存
            if cache_key in self.response_cache:
                return self.response_cache[cache_key]

            # 优化数据结构
            optimized_data = self._optimize_data(data)

            # 序列化
            serialized_data = self._serialize_data(optimized_data)

            # 压缩（如果需要）
            if len(serialized_data) > self.compression_threshold:
                compressed_data = await self._compress_data(
                    serialized_data, method=compression
                )
                response = self._create_compressed_response(
                    compressed_data, compression_method=compression
                )
            else:
                response = FastJSONResponse(content=optimized_data)

            # 缓存响应
            self.response_cache[cache_key] = response

            # 记录性能指标
            duration = (datetime.now() - start_time).total_seconds()
            performance_monitor.record_metric(
                "api_response_optimization_time", duration
            )

            return response

        except Exception as e:
            performance_monitor.record_metric("api_optimization_error", 1)
            raise

    def _generate_cache_key(self, data: Any, request: Request = None) -> str:
        """生成缓存键"""
        if request:
            return f"{request.url.path}:{orjson.dumps(data).decode()}"
        return orjson.dumps(data).decode()

    def _optimize_data(self, data: Any) -> Any:
        """优化数据结构"""
        if isinstance(data, dict):
            return {k: self._optimize_data(v) for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [self._optimize_data(item) for item in data if item is not None]
        return data

    def _serialize_data(self, data: Any) -> bytes:
        """序列化数据"""
        return orjson.dumps(
            data, option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SERIALIZE_UUID
        )

    async def _compress_data(self, data: bytes, method: str = "gzip") -> bytes:
        """压缩数据"""
        if method not in self.compression_methods:
            raise ValueError(f"Unsupported compression method: {method}")

        return await self.compression_methods[method](data)

    async def _compress_gzip(self, data: bytes) -> bytes:
        """使用gzip压缩"""
        return zlib.compress(data)

    async def _compress_snappy(self, data: bytes) -> bytes:
        """使用snappy压缩"""
        return snappy.compress(data)

    def _create_compressed_response(
        self, data: bytes, compression_method: str
    ) -> Response:
        """创建压缩响应"""
        response = Response(content=data, media_type="application/json")
        response.headers["Content-Encoding"] = compression_method
        return response


class BatchRequestOptimizer:
    """批量请求优化器"""

    def __init__(self, max_batch_size: int = 10):
        self.max_batch_size = max_batch_size
        self.batch_cache = TTLCache(maxsize=100, ttl=60)  # 1分钟缓存

    async def optimize_batch_request(
        self, requests: List[Dict], handler: callable
    ) -> List[Any]:
        """优化批量请求处理"""
        # 分批处理
        batches = [
            requests[i : i + self.max_batch_size]
            for i in range(0, len(requests), self.max_batch_size)
        ]

        results = []
        for batch in batches:
            # 检查缓存
            cached_results = self._get_cached_results(batch)

            # 处理未缓存的请求
            uncached_requests = [
                req for req, res in zip(batch, cached_results) if res is None
            ]

            if uncached_requests:
                batch_results = await asyncio.gather(
                    *[handler(req) for req in uncached_requests]
                )

                # 更新缓存
                self._cache_results(uncached_requests, batch_results)

                # 合并结果
                merged_results = self._merge_results(
                    batch, cached_results, uncached_requests, batch_results
                )
            else:
                merged_results = cached_results

            results.extend(merged_results)

        return results

    def _get_cached_results(self, requests: List[Dict]) -> List[Optional[Any]]:
        """获取缓存的结果"""
        return [self.batch_cache.get(self._get_request_key(req)) for req in requests]

    def _cache_results(self, requests: List[Dict], results: List[Any]):
        """缓存结果"""
        for req, res in zip(requests, results):
            self.batch_cache[self._get_request_key(req)] = res

    def _get_request_key(self, request: Dict) -> str:
        """生成请求缓存键"""
        return orjson.dumps(request).decode()

    def _merge_results(
        self,
        original_requests: List[Dict],
        cached_results: List[Optional[Any]],
        uncached_requests: List[Dict],
        new_results: List[Any],
    ) -> List[Any]:
        """合并缓存和新结果"""
        result_map = {
            self._get_request_key(req): res
            for req, res in zip(uncached_requests, new_results)
        }

        return [
            result_map.get(self._get_request_key(req), cached_res)
            for req, cached_res in zip(original_requests, cached_results)
        ]


class FastJSONResponse(JSONResponse):
    """优化的JSON响应类"""

    def render(self, content: Any) -> bytes:
        """使用orjson进行快速JSON序列化"""
        return orjson.dumps(
            content, option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SERIALIZE_UUID
        )


# 创建全局实例
api_optimizer = APIResponseOptimizer()
batch_optimizer = BatchRequestOptimizer()
