"""资源调度服务"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ncod.master.models.device import Device
from ncod.master.core.database import async_session
from ncod.utils.logger import logger
from ncod.utils.cache import redis_cache
from ncod.utils.config import settings


class ResourceScheduler:
    """资源调度服务"""

    def __init__(self):
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._resources: Dict[str, Dict] = {}  # 资源信息
        self._allocations: Dict[str, str] = {}  # 资源分配
        self._priorities: Dict[str, int] = {}  # 资源优先级

    async def start(self):
        """启动调度服务"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._schedule_loop())
        logger.info("资源调度服务已启动")

    async def stop(self):
        """停止调度服务"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("资源调度服务已停止")

    async def _schedule_loop(self):
        """调度循环"""
        while self._running:
            try:
                await self._update_resources()
                await self._schedule_resources()
                await asyncio.sleep(settings.SCHEDULE_INTERVAL)
            except Exception as e:
                logger.error(f"资源调度失败: {e}")
                await asyncio.sleep(5)  # 出错后等待5秒再重试

    async def _update_resources(self):
        """更新资源信息"""
        try:
            async with async_session() as session:
                # 获取所有设备
                result = await session.execute(select(Device))
                devices = result.scalars().all()

                for device in devices:
                    # 获取设备资源信息
                    resource_info = await self._get_resource_info(device)
                    self._resources[device.id] = resource_info

        except Exception as e:
            logger.error(f"更新资源信息失败: {e}")

    async def _get_resource_info(self, device: Device) -> Dict:
        """获取资源信息

        Args:
            device: 设备实例

        Returns:
            Dict: 资源信息
        """
        try:
            # 从缓存获取资源信息
            cache_key = f"resource_info:{device.id}"
            info = await redis_cache.get(cache_key)

            if info:
                return info

            # 获取资源信息
            # TODO: 实现具体的资源信息获取逻辑
            # 可以考虑:
            # 1. CPU使用率
            # 2. 内存使用率
            # 3. 网络带宽
            # 4. 存储空间
            # 5. 设备状态
            info = {
                "timestamp": datetime.now().isoformat(),
                "status": device.status.value,
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "network_usage": 0.0,
                "storage_usage": 0.0,
                "available": True,
            }

            # 缓存资源信息
            await redis_cache.set(cache_key, info, expire=settings.RESOURCE_CACHE_TTL)

            return info

        except Exception as e:
            logger.error(f"获取资源信息失败: {e}")
            return {}

    async def _schedule_resources(self):
        """调度资源"""
        try:
            # 获取待分配的资源
            resources = await self._get_available_resources()

            # 获取资源请求
            requests = await self._get_resource_requests()

            # 按优先级排序请求
            requests.sort(key=lambda x: self._get_request_priority(x), reverse=True)

            # 分配资源
            for request in requests:
                # 找到最合适的资源
                resource = self._find_best_resource(request, resources)
                if resource:
                    # 分配资源
                    await self._allocate_resource(request, resource)
                    # 从可用资源中移除
                    resources.remove(resource)

        except Exception as e:
            logger.error(f"调度资源失败: {e}")

    async def _get_available_resources(self) -> List[str]:
        """获取可用资源

        Returns:
            List[str]: 资源ID列表
        """
        try:
            resources = []
            for resource_id, info in self._resources.items():
                if (
                    info.get("available", False)
                    and resource_id not in self._allocations.values()
                ):
                    resources.append(resource_id)
            return resources

        except Exception as e:
            logger.error(f"获取可用资源失败: {e}")
            return []

    async def _get_resource_requests(self) -> List[Dict]:
        """获取资源请求

        Returns:
            List[Dict]: 请求列表
        """
        try:
            # 从缓存获取请求
            requests = await redis_cache.get("resource_requests")
            if requests:
                return requests

            # TODO: 实现具体的请求获取逻辑
            return []

        except Exception as e:
            logger.error(f"获取资源请求失败: {e}")
            return []

    def _get_request_priority(self, request: Dict) -> int:
        """获取请求优先级

        Args:
            request: 请求信息

        Returns:
            int: 优先级(越大越优先)
        """
        try:
            # 获取基础优先级
            priority = request.get("priority", 0)

            # 应用优先级调整
            # TODO: 实现具体的优先级调整逻辑
            # 可以考虑:
            # 1. 请求等待时间
            # 2. 用户级别
            # 3. 业务重要性
            # 4. 资源紧急程度

            return priority

        except Exception as e:
            logger.error(f"获取请求优先级失败: {e}")
            return 0

    def _find_best_resource(self, request: Dict, resources: List[str]) -> Optional[str]:
        """找到最合适的资源

        Args:
            request: 请求信息
            resources: 可用资源列表

        Returns:
            Optional[str]: 资源ID
        """
        try:
            if not resources:
                return None

            # 计算资源得分
            scores = []
            for resource_id in resources:
                score = self._calculate_resource_score(resource_id, request)
                scores.append((resource_id, score))

            # 按得分排序
            scores.sort(key=lambda x: x[1], reverse=True)

            # 返回得分最高的资源
            return scores[0][0] if scores else None

        except Exception as e:
            logger.error(f"查找最佳资源失败: {e}")
            return None

    def _calculate_resource_score(self, resource_id: str, request: Dict) -> float:
        """计算资源得分

        Args:
            resource_id: 资源ID
            request: 请求信息

        Returns:
            float: 资源得分
        """
        try:
            # 获取资源信息
            info = self._resources.get(resource_id, {})

            # 计算基础得分
            score = 1.0

            # 应用得分调整
            # TODO: 实现具体的得分计算逻辑
            # 可以考虑:
            # 1. 资源利用率
            # 2. 负载均衡
            # 3. 网络延迟
            # 4. 硬件兼容性
            # 5. 地理位置

            return score

        except Exception as e:
            logger.error(f"计算资源得分失败: {e}")
            return 0.0

    async def _allocate_resource(self, request: Dict, resource_id: str):
        """分配资源

        Args:
            request: 请求信息
            resource_id: 资源ID
        """
        try:
            # 更新分配关系
            self._allocations[request["id"]] = resource_id

            # 更新资源状态
            await self._update_resource_status(resource_id, "allocated")

            # 发送分配通知
            await self._notify_allocation(request, resource_id)

            logger.info(f"资源分配成功: {resource_id} -> {request['id']}")

        except Exception as e:
            logger.error(f"分配资源失败: {e}")

    async def _update_resource_status(self, resource_id: str, status: str):
        """更新资源状态

        Args:
            resource_id: 资源ID
            status: 资源状态
        """
        try:
            # 更新资源信息
            if resource_id in self._resources:
                self._resources[resource_id]["status"] = status

            # 更新缓存
            cache_key = f"resource_info:{resource_id}"
            await redis_cache.set(
                cache_key,
                self._resources[resource_id],
                expire=settings.RESOURCE_CACHE_TTL,
            )

        except Exception as e:
            logger.error(f"更新资源状态失败: {e}")

    async def _notify_allocation(self, request: Dict, resource_id: str):
        """发送分配通知

        Args:
            request: 请求信息
            resource_id: 资源ID
        """
        try:
            notification = {
                "timestamp": datetime.now().isoformat(),
                "type": "resource_allocated",
                "request_id": request["id"],
                "resource_id": resource_id,
                "details": {
                    "request": request,
                    "resource": self._resources.get(resource_id, {}),
                },
            }

            # 发送通知
            await redis_cache.publish("resource_notifications", notification)

        except Exception as e:
            logger.error(f"发送分配通知失败: {e}")

    async def request_resource(
        self, request_id: str, requirements: Dict, priority: int = 0
    ) -> bool:
        """请求资源

        Args:
            request_id: 请求ID
            requirements: 资源需求
            priority: 优先级

        Returns:
            bool: 是否成功
        """
        try:
            request = {
                "id": request_id,
                "timestamp": datetime.now().isoformat(),
                "requirements": requirements,
                "priority": priority,
            }

            # 添加到请求队列
            requests = await redis_cache.get("resource_requests") or []
            requests.append(request)

            # 更新请求队列
            await redis_cache.set(
                "resource_requests", requests, expire=settings.REQUEST_QUEUE_TTL
            )

            return True

        except Exception as e:
            logger.error(f"请求资源失败: {e}")
            return False

    async def release_resource(self, request_id: str) -> bool:
        """释放资源

        Args:
            request_id: 请求ID

        Returns:
            bool: 是否成功
        """
        try:
            # 获取分配的资源
            resource_id = self._allocations.get(request_id)
            if not resource_id:
                return False

            # 更新资源状态
            await self._update_resource_status(resource_id, "available")

            # 移除分配关系
            self._allocations.pop(request_id, None)

            # 发送释放通知
            notification = {
                "timestamp": datetime.now().isoformat(),
                "type": "resource_released",
                "request_id": request_id,
                "resource_id": resource_id,
            }

            await redis_cache.publish("resource_notifications", notification)

            logger.info(f"资源释放成功: {resource_id} <- {request_id}")

            return True

        except Exception as e:
            logger.error(f"释放资源失败: {e}")
            return False

    def get_allocation(self, request_id: str) -> Optional[str]:
        """获取资源分配

        Args:
            request_id: 请求ID

        Returns:
            Optional[str]: 资源ID
        """
        return self._allocations.get(request_id)

    def get_resource_info(self, resource_id: str) -> Optional[Dict]:
        """获取资源信息

        Args:
            resource_id: 资源ID

        Returns:
            Optional[Dict]: 资源信息
        """
        return self._resources.get(resource_id)

    async def get_resource_usage(self) -> Dict:
        """获取资源使用情况

        Returns:
            Dict: 使用情况统计
        """
        try:
            total = len(self._resources)
            allocated = len(self._allocations)
            available = len(await self._get_available_resources())

            return {
                "timestamp": datetime.now().isoformat(),
                "total": total,
                "allocated": allocated,
                "available": available,
                "utilization": allocated / total if total > 0 else 0,
            }

        except Exception as e:
            logger.error(f"获取资源使用情况失败: {e}")
            return {}


# 创建全局资源调度器实例
resource_scheduler = ResourceScheduler()
