"""
Sync API Router
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from ..config.dev import DATABASE_CONFIG
from ..database.db import DatabaseManager
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/sync", tags=["sync"])
db = DatabaseManager(DATABASE_CONFIG)


@router.get("/tasks")
async def list_sync_tasks(
    status: Optional[str] = None, current_user: Dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """获取同步任务列表"""
    query = """
        SELECT 
            t.*,
            s.source_cluster_id,
            s.target_cluster_id,
            s.config as sync_config
        FROM tasks t
        JOIN sync_tasks s ON t.id = s.task_id
        WHERE ($1::text IS NULL OR t.status = $1)
        ORDER BY t.created_at DESC
    """
    return await db.fetch(query, status)


@router.get("/tasks/{task_id}")
async def get_sync_task(
    task_id: str, current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取同步任务详情"""
    query = """
        SELECT 
            t.*,
            s.source_cluster_id,
            s.target_cluster_id,
            s.config as sync_config,
            (
                SELECT json_agg(p.*)
                FROM task_progress p
                WHERE p.task_id = t.id
                ORDER BY p.created_at DESC
                LIMIT 100
            ) as progress_history
        FROM tasks t
        JOIN sync_tasks s ON t.id = s.task_id
        WHERE t.id = $1
    """
    task = await db.fetchrow(query, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(task)


@router.post("/tasks")
async def create_sync_task(
    task: Dict[str, Any], current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """创建同步任务"""
    async with db.connection() as conn:
        # 开始事务
        tr = conn.transaction()
        await tr.start()

        try:
            # 创建基本任务
            task_query = """
                INSERT INTO tasks (name, type, status, config)
                VALUES ($1, 'sync', 'pending', $2)
                RETURNING *
            """
            task_record = await conn.fetchrow(
                task_query, task["name"], task.get("config", {})
            )

            # 创建同步任务详情
            sync_query = """
                INSERT INTO sync_tasks (
                    task_id,
                    source_cluster_id,
                    target_cluster_id,
                    config
                )
                VALUES ($1, $2, $3, $4)
                RETURNING *
            """
            sync_record = await conn.fetchrow(
                sync_query,
                task_record["id"],
                task["source_cluster_id"],
                task["target_cluster_id"],
                task.get("sync_config", {}),
            )

            await tr.commit()

            return {**dict(task_record), "sync_config": dict(sync_record)}
        except Exception as e:
            await tr.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.put("/tasks/{task_id}")
async def update_sync_task(
    task_id: str, task: Dict[str, Any], current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """更新同步任务"""
    async with db.connection() as conn:
        tr = conn.transaction()
        await tr.start()

        try:
            # 更新基本任务
            task_query = """
                UPDATE tasks
                SET 
                    name = $2,
                    config = $3,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING *
            """
            task_record = await conn.fetchrow(
                task_query, task_id, task["name"], task.get("config", {})
            )

            if not task_record:
                raise HTTPException(status_code=404, detail="Task not found")

            # 更新同步任务详情
            sync_query = """
                UPDATE sync_tasks
                SET 
                    source_cluster_id = $2,
                    target_cluster_id = $3,
                    config = $4
                WHERE task_id = $1
                RETURNING *
            """
            sync_record = await conn.fetchrow(
                sync_query,
                task_id,
                task["source_cluster_id"],
                task["target_cluster_id"],
                task.get("sync_config", {}),
            )

            await tr.commit()

            return {**dict(task_record), "sync_config": dict(sync_record)}
        except Exception as e:
            await tr.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/tasks/{task_id}")
async def delete_sync_task(
    task_id: str, current_user: Dict = Depends(get_current_user)
) -> Dict[str, str]:
    """删除同步任务"""
    async with db.connection() as conn:
        tr = conn.transaction()
        await tr.start()

        try:
            # 删除同步任务详情
            await conn.execute("DELETE FROM sync_tasks WHERE task_id = $1", task_id)

            # 删除基本任务
            deleted = await conn.fetchval(
                "DELETE FROM tasks WHERE id = $1 RETURNING id", task_id
            )

            if not deleted:
                raise HTTPException(status_code=404, detail="Task not found")

            await tr.commit()
            return {"message": "Task deleted successfully"}
        except Exception as e:
            await tr.rollback()
            raise HTTPException(status_code=400, detail=str(e))
