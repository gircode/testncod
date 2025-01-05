"""任务页面模块"""

# 标准库导入
from datetime import datetime
from typing import Dict, List, Optional

# 第三方库导入
from fastapi import HTTPException, status
from pydantic import BaseModel

# 本地导入
from ncod.core.config import settings
from ncod.core.log import logger
from ncod.models.task import Task, TaskStatus


class TaskPage:
    """任务页面类"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}

    def create_task(
        self, name: str, description: Optional[str] = None, priority: int = 0
    ) -> Task:
        """创建任务

        Args:
            name: 任务名称
            description: 任务描述
            priority: 任务优先级

        Returns:
            新创建的任务
        """
        task = Task(
            name=name,
            description=description or "",
            priority=priority,
            status=TaskStatus.PENDING,
        )
        self.tasks[task.id] = task
        return task

    def update_task_status(
        self, task_id: str, status: TaskStatus, message: Optional[str] = None
    ) -> Task:
        """更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            message: 状态消息

        Returns:
            更新后的任务
        """
        if task_id not in self.tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        task = self.tasks[task_id]
        task.status = status
        if message:
            task.message = message
        return task
