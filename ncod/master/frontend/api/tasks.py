"""
Tasks API Router
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException


class TaskRouter:
    def __init__(self):
        self.router = APIRouter()
        self._setup_routes()
        self._tasks: Dict[str, Dict[str, Any]] = {}  # 添加类型注解

    async def _setup_routes(self):  # 改为异步函数
        @self.router.get("/", response_model=List[Dict[str, Any]])
        async def get_tasks() -> List[Dict[str, Any]]:
            """Get all tasks"""
            return list(self._tasks.values())

        @self.router.post("/")
        async def create_task(task: Dict[str, Any]):
            """Create a new task"""
            task_id = str(len(self._tasks) + 1)
            task["id"] = task_id
            task["created_at"] = datetime.now().isoformat()
            task["status"] = "pending"
            self._tasks[task_id] = task
            return task

        @self.router.get("/{task_id}")
        async def get_task(task_id: str):
            """Get a specific task"""
            if task_id not in self._tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            return self._tasks[task_id]

        @self.router.put("/{task_id}")
        async def update_task(task_id: str, task_update: Dict[str, Any]):
            """Update a task"""
            if task_id not in self._tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            task = self._tasks[task_id]
            task.update(task_update)
            task["updated_at"] = datetime.now().isoformat()
            return task

        @self.router.delete("/{task_id}")
        async def delete_task(task_id: str):
            """Delete a task"""
            if task_id not in self._tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            del self._tasks[task_id]
            return {"message": "Task deleted"}


def get_task_status() -> Dict[str, Any]:
    """获取任务状态"""
    updated_at = datetime.now().isoformat()
    return {"updated_at": updated_at, "status": "active"}  # 添加状态信息
