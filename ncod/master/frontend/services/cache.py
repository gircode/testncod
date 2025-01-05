"""Cache模块"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import redis

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, host="localhost", port=6379, db=0, password=None):
        self.redis = redis.Redis(
            host=host, port=port, db=db, password=password, decode_responses=True
        )

        # 默认缓存时间（秒）
        self.default_ttl = 300  # 5分钟

        # 缓存键前缀
        self.key_prefix = "ncod:"

        # 缓存键模式
        self.key_patterns = {
            "device": "device:{id}",
            "device_metrics": "device:{id}:metrics",
            "device_status": "device:{id}:status",
            "device_group": "device_group:{id}",
            "user": "user:{id}",
            "task": "task:{id}",
            "alert": "alert:{id}",
            "security_scan": "security_scan:{id}",
            "backup": "backup:{id}",
        }

    def _build_key(self, pattern: str, **kwargs) -> str:
        """构建缓存键"""
        key = self.key_patterns[pattern].format(**kwargs)
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存数据"""
        try:
            data = json.dumps(value)
            return self.redis.set(key, data, ex=ttl or self.default_ttl)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存数据"""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        try:
            return bool(self.redis.expire(key, ttl))
        except Exception as e:
            logger.error(f"Redis expire error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> bool:
        """清除匹配模式的所有键"""
        try:
            pattern = f"{self.key_prefix}{pattern}*"
            keys = self.redis.keys(pattern)
            if keys:
                return bool(self.redis.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"Redis clear pattern error: {e}")
            return False

    # 设备相关缓存方法
    async def get_device(self, device_id: int) -> Optional[Dict]:
        """获取设备缓存"""
        key = self._build_key("device", id=device_id)
        return await self.get(key)

    async def set_device(self, device_id: int, data: Dict) -> bool:
        """设置设备缓存"""
        key = self._build_key("device", id=device_id)
        return await self.set(key, data)

    async def get_device_metrics(self, device_id: int) -> Optional[List[Dict]]:
        """获取设备指标缓存"""
        key = self._build_key("device_metrics", id=device_id)
        return await self.get(key)

    async def set_device_metrics(
        self, device_id: int, metrics: List[Dict], ttl: int = 60
    ) -> bool:
        """设置设备指标缓存"""
        key = self._build_key("device_metrics", id=device_id)
        return await self.set(key, metrics, ttl)

    async def get_device_status(self, device_id: int) -> Optional[str]:
        """获取设备状态缓存"""
        key = self._build_key("device_status", id=device_id)
        return await self.get(key)

    async def set_device_status(
        self, device_id: int, status: str, ttl: int = 30
    ) -> bool:
        """设置设备状态缓存"""
        key = self._build_key("device_status", id=device_id)
        return await self.set(key, status, ttl)

    # 设备组相关缓存方法
    async def get_device_group(self, group_id: int) -> Optional[Dict]:
        """获取设备组缓存"""
        key = self._build_key("device_group", id=group_id)
        return await self.get(key)

    async def set_device_group(self, group_id: int, data: Dict) -> bool:
        """设置设备组缓存"""
        key = self._build_key("device_group", id=group_id)
        return await self.set(key, data)

    # 任务相关缓存方法
    async def get_task(self, task_id: int) -> Optional[Dict]:
        """获取任务缓存"""
        key = self._build_key("task", id=task_id)
        return await self.get(key)

    async def set_task(self, task_id: int, data: Dict) -> bool:
        """设置任务缓存"""
        key = self._build_key("task", id=task_id)
        return await self.set(key, data)

    # 告警相关缓存方法
    async def get_alert(self, alert_id: int) -> Optional[Dict]:
        """获取告警缓存"""
        key = self._build_key("alert", id=alert_id)
        return await self.get(key)

    async def set_alert(self, alert_id: int, data: Dict) -> bool:
        """设置告警缓存"""
        key = self._build_key("alert", id=alert_id)
        return await self.set(key, data)

    # 用户相关缓存方法
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """获取用户缓存"""
        key = self._build_key("user", id=user_id)
        return await self.get(key)

    async def set_user(self, user_id: int, data: Dict) -> bool:
        """设置用户缓存"""
        key = self._build_key("user", id=user_id)
        return await self.set(key, data)

    # 安全扫描相关缓存方法
    async def get_security_scan(self, scan_id: int) -> Optional[Dict]:
        """获取安全扫描缓存"""
        key = self._build_key("security_scan", id=scan_id)
        return await self.get(key)

    async def set_security_scan(self, scan_id: int, data: Dict) -> bool:
        """设置安全扫描缓存"""
        key = self._build_key("security_scan", id=scan_id)
        return await self.set(key, data)

    # 备份相关缓存方法
    async def get_backup(self, backup_id: int) -> Optional[Dict]:
        """获取备份缓存"""
        key = self._build_key("backup", id=backup_id)
        return await self.get(key)

    async def set_backup(self, backup_id: int, data: Dict) -> bool:
        """设置备份缓存"""
        key = self._build_key("backup", id=backup_id)
        return await self.set(key, data)


# 创建全局缓存实例
cache = RedisCache()
