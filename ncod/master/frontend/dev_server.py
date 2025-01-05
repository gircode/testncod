"""
Development Server
"""

import secrets
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Awaitable, Dict, cast

import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pytest import FixtureRequest

from .types.fixtures import AsyncFixture, FixtureResult

# 获取基础路径
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"

# 开发服务器配置
DEV_SERVER = {"host": "localhost", "port": 8000, "reload": True, "debug": True}

# 模拟数据配置
MOCK_DATA = {
    "clusters": [
        {
            "id": "1",
            "name": "测试集群1",
            "status": "active",
            "node_count": 3,
            "last_heartbeat": "2024-03-20T10:00:00",
        },
        {
            "id": "2",
            "name": "测试集群2",
            "status": "inactive",
            "node_count": 2,
            "last_heartbeat": "2024-03-20T09:30:00",
        },
    ],
    "tasks": [
        {
            "id": "1",
            "name": "数据同步任务 #1",
            "status": "completed",
            "progress": 100,
            "created_at": "2024-03-20T08:00:00",
            "completed_at": "2024-03-20T08:30:00",
            "type": "sync",
        },
        {
            "id": "2",
            "name": "数据备份任务 #1",
            "status": "running",
            "progress": 45,
            "created_at": "2024-03-20T09:00:00",
            "type": "backup",
        },
        {
            "id": "3",
            "name": "系统检查任务 #1",
            "status": "failed",
            "progress": 60,
            "created_at": "2024-03-20T08:45:00",
            "error": "连接超时",
            "type": "check",
        },
        {
            "id": "4",
            "name": "数据同步任务 #2",
            "status": "pending",
            "progress": 0,
            "created_at": "2024-03-20T09:15:00",
            "type": "sync",
        },
    ],
    "performance": {
        "cpu_usage": [
            {"timestamp": "2024-03-20T09:00:00", "value": 45},
            {"timestamp": "2024-03-20T09:05:00", "value": 52},
            {"timestamp": "2024-03-20T09:10:00", "value": 48},
        ],
        "memory_usage": [
            {"timestamp": "2024-03-20T09:00:00", "value": 62},
            {"timestamp": "2024-03-20T09:05:00", "value": 65},
            {"timestamp": "2024-03-20T09:10:00", "value": 63},
        ],
    },
}

app = FastAPI(debug=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 配置模板
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

security = HTTPBasic()


def verify_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """验证基本认证"""
    correct_username = "admin"
    correct_password = "admin"

    is_username_correct = secrets.compare_digest(
        credentials.username.encode("utf8"), correct_username.encode("utf8")
    )
    is_password_correct = secrets.compare_digest(
        credentials.password.encode("utf8"), correct_password.encode("utf8")
    )

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/")
async def index(request: Request, username: str = Depends(verify_auth)):
    """渲染主页"""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "username": username,
            "clusters": MOCK_DATA["clusters"],
            "tasks": MOCK_DATA["tasks"],
            "performance": MOCK_DATA["performance"],
        },
    )


@app.get("/api/clusters")
async def get_clusters(_: str = Depends(verify_auth)):
    """获取集群数据"""
    return MOCK_DATA["clusters"]


@app.get("/api/tasks")
async def get_tasks(_: str = Depends(verify_auth)):
    """获取任务数据"""
    return MOCK_DATA["tasks"]


@app.get("/api/performance")
async def get_performance(_: str = Depends(verify_auth)):
    """获取性能数据"""
    return MOCK_DATA["performance"]


async def async_func():
    return await some_async_operation()


fixture = FixtureFunction(simple_func, async_func)


@app.get("/api/metrics/performance")
async def get_metrics_performance(_: str = Depends(verify_auth)):
    """获取性能指标数据"""
    return {
        "metrics": {
            "cpu_usage": MOCK_DATA["performance"]["cpu_usage"][-1]["value"],
            "memory_usage": MOCK_DATA["performance"]["memory_usage"][-1]["value"],
            "completed_tasks": 3,
            "total_tasks": 5,
        }
    }


@app.post("/api/tasks")
async def create_task(task_data: dict, _: str = Depends(verify_auth)):
    """创建新任务"""
    task_id = str(len(MOCK_DATA["tasks"]) + 1)
    new_task = {
        "id": task_id,
        "name": f"{task_data['type']}任务 #{task_id}",
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "type": task_data["type"],
    }
    MOCK_DATA["tasks"].append(new_task)
    return new_task


@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, _: str = Depends(verify_auth)):
    """取消任务"""
    task = next((t for t in MOCK_DATA["tasks"] if t["id"] == task_id), None)
    if task:
        task["status"] = "cancelled"
        return {"message": "Task cancelled"}
    raise HTTPException(status_code=404, detail="Task not found")


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str, _: str = Depends(verify_auth)):
    """获取任务详情"""
    task = next((t for t in MOCK_DATA["tasks"] if t["id"] == task_id), None)
    if task:
        return task
    raise HTTPException(status_code=404, detail="Task not found")


@app.get("/settings")
async def settings_page(request: Request, username: str = Depends(verify_auth)):
    """系统设置页面"""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "username": username,
            "settings": {
                "system_name": "NCOD System",
                "data_path": "/data",
                "log_level": "INFO",
                "host": "0.0.0.0",
                "port": 8000,
                "allowed_ips": ["127.0.0.1"],
                "backup_path": "/backup",
                "backup_interval": "daily",
                "backup_keep_count": 7,
                "ssl_enabled": False,
                "ssl_cert_path": "",
                "ssl_key_path": "",
                "worker_count": 4,
                "max_connections": 1000,
                "timeout": 30,
            },
        },
    )


@app.post("/api/settings/{section}")
async def update_settings(section: str, settings: dict, _: str = Depends(verify_auth)):
    """更新设置"""
    # 这里应该实现实际的设置保存逻辑
    return {"message": f"{section} settings updated"}


@app.get("/organization")
async def organization_page(request: Request, username: str = Depends(verify_auth)):
    """组织架构管理页面"""
    return templates.TemplateResponse(
        "organization.html",
        {
            "request": request,
            "username": username,
            "departments": [
                {
                    "id": "1",
                    "name": "总部",
                    "children": [
                        {"id": "2", "name": "研发部", "children": []},
                        {"id": "3", "name": "运维部", "children": []},
                    ],
                }
            ],
            "pipelines": [
                {
                    "id": "1",
                    "name": "主数据同步管线",
                    "status": "active",
                    "department": "研发部",
                    "created_at": "2024-03-20T08:00:00",
                    "nodes": [
                        {
                            "type": "master",
                            "address": "192.168.1.100:8000",
                            "status": "active",
                        },
                        {
                            "type": "slave",
                            "address": "192.168.1.101:8000",
                            "status": "active",
                        },
                    ],
                }
            ],
        },
    )


@app.get("/api/departments/{dept_id}")
async def get_department(dept_id: str, _: str = Depends(verify_auth)):
    """获取部门信息"""
    # 模拟数据
    return {"id": dept_id, "name": "研发部", "parent_id": "1"}


@app.post("/api/departments")
async def create_department(dept: dict, _: str = Depends(verify_auth)):
    """创建部门"""
    return {"id": "new_id", **dept}


@app.put("/api/departments/{dept_id}")
async def update_department(dept_id: str, dept: dict, _: str = Depends(verify_auth)):
    """更新部门"""
    return {"id": dept_id, **dept}


@app.delete("/api/departments/{dept_id}")
async def delete_department(dept_id: str, _: str = Depends(verify_auth)):
    """删除部门"""
    return {"message": "Department deleted"}


@app.get("/api/pipelines/{pipeline_id}")
async def get_pipeline(pipeline_id: str, _: str = Depends(verify_auth)):
    """获取管线信息"""
    return {
        "id": pipeline_id,
        "name": "主数据同步管线",
        "department_id": "2",
        "nodes": [
            {"type": "master", "address": "192.168.1.100:8000"},
            {"type": "slave", "address": "192.168.1.101:8000"},
        ],
    }


@app.post("/api/pipelines")
async def create_pipeline(pipeline: dict, _: str = Depends(verify_auth)):
    """创建管线"""
    return {"id": "new_id", **pipeline}


@app.put("/api/pipelines/{pipeline_id}")
async def update_pipeline(
    pipeline_id: str, pipeline: dict, _: str = Depends(verify_auth)
):
    """更新管线"""
    return {"id": pipeline_id, **pipeline}


@app.delete("/api/pipelines/{pipeline_id}")
async def delete_pipeline(pipeline_id: str, _: str = Depends(verify_auth)):
    """删除管线"""
    return {"message": "Pipeline deleted"}


# 监控相关路由
@app.get("/monitor/nodes")
async def nodes_monitor(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "monitor/nodes.html",
        {"request": request, "username": username, "active_page": "nodes"},
    )


@app.get("/monitor/performance")
async def performance_monitor(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "monitor/performance.html",
        {"request": request, "username": username, "active_page": "performance"},
    )


# 任务管理路由
@app.get("/tasks")
async def tasks_list(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "tasks/list.html",
        {"request": request, "username": username, "active_page": "tasks"},
    )


@app.get("/tasks/scheduler")
async def task_scheduler(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "tasks/scheduler.html",
        {"request": request, "username": username, "active_page": "scheduler"},
    )


@app.get("/tasks/history")
async def task_history(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "tasks/history.html",
        {"request": request, "username": username, "active_page": "history"},
    )


# 数据管理路由
@app.get("/data/sync")
async def data_sync(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "data/sync.html",
        {"request": request, "username": username, "active_page": "sync"},
    )


@app.get("/data/backup")
async def data_backup(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "data/backup.html",
        {"request": request, "username": username, "active_page": "backup"},
    )


@app.get("/data/recovery")
async def data_recovery(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "data/recovery.html",
        {"request": request, "username": username, "active_page": "recovery"},
    )


# 用户和权限路由
@app.get("/users")
async def users_management(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "users/list.html",
        {"request": request, "username": username, "active_page": "users"},
    )


@app.get("/roles")
async def roles_management(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "roles/list.html",
        {"request": request, "username": username, "active_page": "roles"},
    )


# 日志路由
@app.get("/logs/system")
async def system_logs(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "logs/system.html",
        {"request": request, "username": username, "active_page": "system_logs"},
    )


@app.get("/logs/audit")
async def audit_logs(request: Request, username: str = Depends(verify_auth)):
    return templates.TemplateResponse(
        "logs/audit.html",
        {"request": request, "username": username, "active_page": "audit_logs"},
    )


# 添加全局变量定义
cpu_usage: float = 0.0
memory_usage: float = 0.0
status: Dict[str, Any] = {"status": "running", "uptime": 3600, "connections": 100}


async def get_cpu_usage() -> float:
    """获取CPU使用率"""
    global cpu_usage
    # 实现CPU使用率获取逻辑
    return cpu_usage


async def get_memory_usage() -> float:
    """获取内存使用率"""
    global memory_usage
    # 实现内存使用率获取逻辑
    return memory_usage


async def get_status() -> Dict[str, Any]:
    """获取系统状态"""
    global status
    # 实现状态获取逻辑
    return status


class MetricsFixtures:
    """系统指标相关的fixture"""

    @staticmethod
    @pytest_asyncio.fixture
    async def test_cpu_usage(request: FixtureRequest) -> FixtureResult[float]:
        """测试CPU使用率获取"""
        value = await get_cpu_usage()
        yield value

    @staticmethod
    @pytest_asyncio.fixture
    async def test_memory_usage(request: FixtureRequest) -> FixtureResult[float]:
        """测试内存使用率获取"""
        value = await get_memory_usage()
        yield value

    @staticmethod
    @pytest_asyncio.fixture
    async def test_status(request: FixtureRequest) -> FixtureResult[Dict[str, Any]]:
        """测试系统状态获取"""
        value = await get_status()
        yield value


# 将fixture方法转换为正确的类型
test_cpu_usage = cast(AsyncFixture[float], MetricsFixtures.test_cpu_usage)
test_memory_usage = cast(AsyncFixture[float], MetricsFixtures.test_memory_usage)
test_status = cast(AsyncFixture[Dict[str, Any]], MetricsFixtures.test_status)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "dev_server:app",
        host=DEV_SERVER["host"],
        port=DEV_SERVER["port"],
        reload=DEV_SERVER["reload"],
    )
