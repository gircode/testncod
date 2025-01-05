"""
同步服务
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.sync import SyncItem, SyncRecord
from ..schemas.sync import SyncItemCreate, SyncRecordCreate, SyncRequest, SyncResponse


class SyncService:
    """同步服务"""

    def __init__(self, db: AsyncSession):
        """初始化同步服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self._running = False
        self._task = None

    async def start(self) -> None:
        """启动同步"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._sync_loop())

    async def stop(self) -> None:
        """停止同步"""
        if not self._running:
            return

        self._running = False
        if self._task:
            await self._task
            self._task = None

    async def _sync_loop(self) -> None:
        """同步循环"""
        while self._running:
            try:
                # 获取待同步记录
                result = await self.db.execute(
                    select(SyncRecord)
                    .filter(SyncRecord.status == "pending")
                    .order_by(SyncRecord.start_time)
                )
                records = result.scalars().all()

                # 处理每个同步记录
                for record in records:
                    await self._process_sync_record(record)

                # 等待下一次同步
                await asyncio.sleep(30)

            except Exception as e:
                # 记录错误但继续运行
                print(f"同步错误: {str(e)}")
                await asyncio.sleep(30)

    async def _process_sync_record(self, record: SyncRecord) -> None:
        """处理同步记录

        Args:
            record: 同步记录
        """
        try:
            # 更新状态为运行中
            record.status = "running"
            await self.db.commit()

            # 获取同步项目
            result = await self.db.execute(
                select(SyncItem)
                .filter(SyncItem.record_id == record.id)
                .filter(SyncItem.status == "pending")
            )
            items = result.scalars().all()

            # 更新总数
            record.total_items = len(items)
            await self.db.commit()

            # 处理每个同步项目
            for item in items:
                try:
                    await self._process_sync_item(item)
                    record.processed_items += 1
                except Exception as e:
                    record.failed_items += 1
                    item.status = "failed"
                    item.error_message = str(e)
                await self.db.commit()

            # 更新状态为完成
            record.status = "completed"
            record.end_time = datetime.utcnow()
            await self.db.commit()

        except Exception as e:
            # 更新状态为失败
            record.status = "failed"
            record.error_message = str(e)
            record.end_time = datetime.utcnow()
            await self.db.commit()

    async def _process_sync_item(self, item: SyncItem) -> None:
        """处理同步项目

        Args:
            item: 同步项目
        """
        # TODO: 实现具体的同步逻辑
        item.status = "success"
        item.timestamp = datetime.utcnow()

    async def sync_data(self, request: SyncRequest) -> SyncResponse:
        """同步数据

        Args:
            request: 同步请求

        Returns:
            SyncResponse: 同步响应
        """
        # 创建同步记录
        record = SyncRecord(
            device_id=request.device_id,
            sync_type=request.sync_type,
            status="pending",
            start_time=datetime.utcnow(),
            metadata=request.metadata,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        # 创建同步项目
        for item_data in request.items:
            item = SyncItem(
                record_id=record.id,
                item_type=item_data["type"],
                item_id=item_data["id"],
                status="pending",
                timestamp=datetime.utcnow(),
                metadata=item_data.get("metadata"),
            )
            self.db.add(item)
        await self.db.commit()

        return SyncResponse(
            record_id=record.id,
            status=record.status,
            total_items=len(request.items),
            processed_items=0,
            failed_items=0,
        )

    async def get_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        # 获取最近的同步记录
        result = await self.db.execute(
            select(SyncRecord).order_by(SyncRecord.start_time.desc()).limit(1)
        )
        latest_record = result.scalar_one_or_none()

        # 获取运行中的同步记录
        result = await self.db.execute(
            select(SyncRecord).filter(SyncRecord.status == "running")
        )
        running_records = result.scalars().all()

        return {
            "last_sync": latest_record.to_dict() if latest_record else None,
            "running_syncs": [record.to_dict() for record in running_records],
            "is_running": self._running,
        }

    async def get_history(
        self, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取同步历史

        Args:
            skip: 跳过数量
            limit: 限制数量

        Returns:
            List[Dict[str, Any]]: 同步历史
        """
        result = await self.db.execute(
            select(SyncRecord)
            .order_by(SyncRecord.start_time.desc())
            .offset(skip)
            .limit(limit)
        )
        records = result.scalars().all()
        return [record.to_dict() for record in records]

    async def reset(self) -> None:
        """重置同步"""
        # 停止同步
        await self.stop()

        # 更新所有运行中的记录为失败
        result = await self.db.execute(
            select(SyncRecord).filter(SyncRecord.status == "running")
        )
        running_records = result.scalars().all()

        for record in running_records:
            record.status = "failed"
            record.error_message = "同步被重置"
            record.end_time = datetime.utcnow()

        await self.db.commit()
