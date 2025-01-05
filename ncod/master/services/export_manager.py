from datetime import datetime, timedelta
import asyncio
import os
from typing import Dict, Optional
import pandas as pd
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class ExportTask:
    def __init__(self, task_id: str, file_path: str):
        self.task_id = task_id
        self.file_path = file_path
        self.status = "pending"
        self.progress = 0
        self.error = None
        self.created_at = datetime.utcnow()


class ExportManager:
    def __init__(self):
        self.tasks: Dict[str, ExportTask] = {}
        self.chunk_size = 1000  # 每次处理的记录数
        self.export_dir = "temp/exports"
        self.cleanup_interval = 6 * 3600  # 6小时清理一次

        # 确保导出目录存在
        os.makedirs(self.export_dir, exist_ok=True)

        # 启动清理任务
        asyncio.create_task(self._cleanup_loop())

    async def create_export_task(self, task_id: str) -> ExportTask:
        """创建导出任务"""
        file_path = os.path.join(
            self.export_dir,
            f"export_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )
        task = ExportTask(task_id, file_path)
        self.tasks[task_id] = task
        return task

    def get_task_status(self, task_id: str) -> Optional[ExportTask]:
        """获取任务状态"""
        return self.tasks.get(task_id)

    async def export_device_stats(
        self,
        db: Session,
        device_id: int,
        task: ExportTask,
        template_path: Optional[str] = None,
    ):
        """导出设备统计数据"""
        try:
            task.status = "processing"

            # 使用模板文件(如果有)
            writer = pd.ExcelWriter(
                task.file_path,
                engine="xlsxwriter",
                engine_kwargs={"options": {"constant_memory": True}},
            )

            # 分块处理统计数据
            usage_stats = []
            offset = 0
            while True:
                stats_chunk = await self._get_stats_chunk(
                    db, device_id, offset, self.chunk_size
                )
                if not stats_chunk:
                    break

                usage_stats.extend(stats_chunk)
                offset += self.chunk_size
                task.progress = min(90, int(task.progress + 10))

            # 写入统计数据
            pd.DataFrame(usage_stats).to_excel(
                writer, sheet_name="使用统计", index=False
            )

            # 分块处理日志数据
            connection_logs = []
            offset = 0
            while True:
                logs_chunk = await self._get_logs_chunk(
                    db, device_id, offset, self.chunk_size
                )
                if not logs_chunk:
                    break

                connection_logs.extend(logs_chunk)
                offset += self.chunk_size
                task.progress = min(99, int(task.progress + 5))

            # 写入日志数据
            pd.DataFrame(connection_logs).to_excel(
                writer, sheet_name="连接记录", index=False
            )

            writer.close()
            task.status = "completed"
            task.progress = 100

        except Exception as e:
            logger.error(f"Export error: {e}")
            task.status = "failed"
            task.error = str(e)

    async def _get_stats_chunk(
        self, db: Session, device_id: int, offset: int, limit: int
    ) -> list:
        """分块获取统计数据"""
        stats = (
            db.query(DeviceUsageStats)
            .filter_by(device_id=device_id)
            .order_by(DeviceUsageStats.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            {
                "用户": stat.user.username,
                "总使用时长(小时)": round(stat.total_usage_time, 2),
                "连接次数": stat.connection_count,
                "失败次数": stat.failed_connection_count,
                "最后连接时间": stat.last_connected,
                "最后断开时间": stat.last_disconnected,
            }
            for stat in stats
        ]

    async def _get_logs_chunk(
        self, db: Session, device_id: int, offset: int, limit: int
    ) -> list:
        """分块获取日志数据"""
        logs = (
            db.query(DeviceUsageLog)
            .filter_by(device_id=device_id)
            .order_by(DeviceUsageLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            {
                "用户": log.user.username,
                "操作": log.action,
                "状态": log.status,
                "错误信息": log.error_message,
                "时间": log.created_at,
            }
            for log in logs
        ]

    async def _cleanup_loop(self):
        """定期清理过期文件"""
        while True:
            try:
                await self._cleanup_expired_files()
                await asyncio.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _cleanup_expired_files(self):
        """清理过期文件和任务"""
        now = datetime.utcnow()
        expired_time = now - timedelta(hours=6)

        # 清理过期任务
        expired_tasks = [
            task_id
            for task_id, task in self.tasks.items()
            if task.created_at < expired_time
        ]

        for task_id in expired_tasks:
            task = self.tasks.pop(task_id)
            try:
                if os.path.exists(task.file_path):
                    os.remove(task.file_path)
            except Exception as e:
                logger.error(f"Error removing file {task.file_path}: {e}")

        # 清理遗留文件
        for filename in os.listdir(self.export_dir):
            file_path = os.path.join(self.export_dir, filename)
            try:
                if os.path.getctime(file_path) < expired_time.timestamp():
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Error removing file {file_path}: {e}")
