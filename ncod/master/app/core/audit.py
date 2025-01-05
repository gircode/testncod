"""
审计日志模块
"""

import json
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as aioredis
from app.core.config import settings
from fastapi import HTTPException, Request
from pydantic import BaseModel


class AuditAction(str, Enum):
    """审计动作"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    EXECUTE = "execute"


class AuditResourceType(str, Enum):
    """审计资源类型"""

    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    DEVICE = "device"
    SLAVE = "slave"
    METRIC = "metric"
    SETTING = "setting"
    FILE = "file"


class AuditLogEntry(BaseModel):
    """审计日志条目"""

    timestamp: int
    user_id: str
    action: AuditAction
    resource_type: AuditResourceType
    resource_id: str
    status: str
    details: Dict[str, Any]
    client_ip: str
    user_agent: str


class AuditLogger:
    """审计日志记录器"""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.prefix = "audit:"
        self.retention = settings.AUDIT_LOG_RETENTION_DAYS * 24 * 60 * 60

    async def setup(self):
        """初始化Redis连接"""
        if not self.redis:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )

    async def log(
        self,
        user_id: str,
        action: AuditAction,
        resource_type: AuditResourceType,
        resource_id: str,
        status: str,
        details: Dict[str, Any],
        request: Request,
    ):
        """记录审计日志"""
        if not settings.AUDIT_LOG_ENABLED:
            return

        await self.setup()
        if not self.redis:
            return

        # 创建日志条目
        entry = AuditLogEntry(
            timestamp=int(time.time()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details=details,
            client_ip=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
        )

        # 保存日志
        await self.redis.zadd(
            f"{self.prefix}{resource_type}", {json.dumps(entry.dict()): entry.timestamp}
        )

        # 清理过期日志
        await self.cleanup()

    async def get_logs(
        self,
        resource_type: Optional[AuditResourceType] = None,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogEntry]:
        """获取审计日志"""
        await self.setup()
        if not self.redis:
            return []

        if start_time is None:
            start_time = 0
        if end_time is None:
            end_time = int(time.time())

        # 获取指定类型的日志
        if resource_type:
            keys = [f"{self.prefix}{resource_type}"]
        else:
            # 获取所有类型的日志
            keys = []
            for rt in AuditResourceType:
                keys.append(f"{self.prefix}{rt}")

        # 获取日志条目
        all_entries = []
        for key in keys:
            entries = await self.redis.zrangebyscore(
                key, start_time, end_time, start=offset, num=limit, withscores=True
            )
            for entry_json, score in entries:
                entry = json.loads(entry_json)
                if (not user_id or entry["user_id"] == user_id) and (
                    not action or entry["action"] == action
                ):
                    all_entries.append(AuditLogEntry(**entry))

        # 按时间戳排序
        all_entries.sort(key=lambda x: x.timestamp, reverse=True)

        return all_entries[:limit]

    async def get_user_activity(
        self,
        user_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Dict[str, int]:
        """获取用户活动统计"""
        await self.setup()
        if not self.redis:
            return {}

        if start_time is None:
            start_time = int(time.time()) - 24 * 60 * 60  # 默认查询最近24小时
        if end_time is None:
            end_time = int(time.time())

        # 统计各类操作次数
        activity = {}
        for action in AuditAction:
            count = 0
            for rt in AuditResourceType:
                key = f"{self.prefix}{rt}"
                entries = await self.redis.zrangebyscore(key, start_time, end_time)
                for entry_json in entries:
                    entry = json.loads(entry_json)
                    if entry["user_id"] == user_id and entry["action"] == action:
                        count += 1
            activity[action] = count

        return activity

    async def get_resource_activity(
        self,
        resource_type: AuditResourceType,
        resource_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[AuditLogEntry]:
        """获取资源活动记录"""
        await self.setup()
        if not self.redis:
            return []

        if start_time is None:
            start_time = int(time.time()) - 24 * 60 * 60  # 默认查询最近24小时
        if end_time is None:
            end_time = int(time.time())

        # 获取资源的所有操作记录
        key = f"{self.prefix}{resource_type}"
        entries = await self.redis.zrangebyscore(key, start_time, end_time)

        # 过滤指定资源的记录
        resource_entries = []
        for entry_json in entries:
            entry = json.loads(entry_json)
            if entry["resource_id"] == resource_id:
                resource_entries.append(AuditLogEntry(**entry))

        # 按时间戳排序
        resource_entries.sort(key=lambda x: x.timestamp, reverse=True)

        return resource_entries

    async def cleanup(self):
        """清理过期日志"""
        await self.setup()
        if not self.redis:
            return

        # 获取截止时间
        cutoff = int(time.time()) - self.retention

        # 清理各类型的过期日志
        for rt in AuditResourceType:
            key = f"{self.prefix}{rt}"
            await self.redis.zremrangebyscore(key, "-inf", cutoff)

    async def backup(self):
        """备份审计日志"""
        if not settings.AUDIT_LOG_BACKUP_ENABLED:
            return

        await self.setup()
        if not self.redis:
            return

        # 获取当前时间
        now = datetime.now()
        backup_time = int(now.timestamp())

        # 备份各类型的日志
        for rt in AuditResourceType:
            key = f"{self.prefix}{rt}"
            entries = await self.redis.zrange(key, 0, -1, withscores=True)

            if entries:
                # 创建备份
                backup_key = f"{key}:backup:{backup_time}"
                for entry_json, score in entries:
                    await self.redis.zadd(backup_key, {entry_json: score})

    async def cleanup_backups(self):
        """清理过期备份"""
        await self.setup()
        if not self.redis:
            return

        # 获取所有备份键
        backup_keys = []
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(
                cursor, match=f"{self.prefix}*:backup:*", count=100
            )
            backup_keys.extend(keys)
            if cursor == 0:
                break

        # 删除过期备份
        for key in backup_keys:
            try:
                backup_time = int(key.split(":")[-1])
                if backup_time < int(time.time()) - self.retention:
                    await self.redis.delete(key)
            except (ValueError, IndexError):
                continue
