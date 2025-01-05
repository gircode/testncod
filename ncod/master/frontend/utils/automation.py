"""Automation模块"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from queue import Queue
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp
import paramiko
import schedule

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class TaskResult:
    """任务结果"""

    success: bool
    message: str
    data: Any = None
    error: Optional[Exception] = None


class Task:
    """任务基类"""

    def __init__(
        self,
        task_id: str,
        name: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        retry_count: int = 3,
        retry_interval: int = 60,
    ):
        self.task_id = task_id
        self.name = name
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.retry_count = retry_count
        self.retry_interval = retry_interval
        self.current_retry = 0
        self.start_time = None
        self.end_time = None
        self.result = None
        self.error = None

    async def execute(self) -> TaskResult:
        """执行任务"""
        raise NotImplementedError

    async def retry(self) -> TaskResult:
        """重试任务"""
        while self.current_retry < self.retry_count:
            self.current_retry += 1
            logger.info(f"Retrying task {self.task_id}, attempt {self.current_retry}")

            # 等待重试间隔
            await asyncio.sleep(self.retry_interval)

            try:
                result = await self.execute()
                if result.success:
                    return result
            except Exception as e:
                logger.error(f"Retry failed: {e}")

        return TaskResult(
            success=False,
            message=f"Task failed after {self.retry_count} retries",
            error=self.error,
        )


class HttpTask(Task):
    """HTTP请求任务"""

    def __init__(
        self,
        task_id: str,
        name: str,
        url: str,
        method: str = "GET",
        headers: Dict = None,
        data: Any = None,
        timeout: int = 30,
        **kwargs,
    ):
        super().__init__(task_id, name, **kwargs)
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.data = data
        self.timeout = timeout

    async def execute(self) -> TaskResult:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=self.method,
                    url=self.url,
                    headers=self.headers,
                    json=self.data,
                    timeout=self.timeout,
                ) as response:
                    data = await response.json()
                    return TaskResult(
                        success=response.status < 400,
                        message=f"HTTP {response.status}",
                        data=data,
                    )
        except Exception as e:
            self.error = e
            return TaskResult(success=False, message=str(e), error=e)


class ShellTask(Task):
    """Shell命令任务"""

    def __init__(
        self,
        task_id: str,
        name: str,
        command: str,
        working_dir: str = None,
        env: Dict = None,
        timeout: int = 300,
        **kwargs,
    ):
        super().__init__(task_id, name, **kwargs)
        self.command = command
        self.working_dir = working_dir
        self.env = env or {}
        self.timeout = timeout

    async def execute(self) -> TaskResult:
        try:
            # 合并环境变量
            env = {**os.environ.copy(), **self.env}

            # 执行命令
            process = await asyncio.create_subprocess_shell(
                self.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
                env=env,
            )

            # 等待命令完成
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError(f"Command timed out after {self.timeout} seconds")

            # 检查结果
            if process.returncode == 0:
                return TaskResult(
                    success=True,
                    message="Command executed successfully",
                    data={"stdout": stdout.decode(), "stderr": stderr.decode()},
                )
            else:
                return TaskResult(
                    success=False,
                    message=f"Command failed with exit code {process.returncode}",
                    data={"stdout": stdout.decode(), "stderr": stderr.decode()},
                )

        except Exception as e:
            self.error = e
            return TaskResult(success=False, message=str(e), error=e)


class SSHTask(Task):
    """SSH远程任务"""

    def __init__(
        self,
        task_id: str,
        name: str,
        host: str,
        command: str,
        username: str = None,
        password: str = None,
        key_filename: str = None,
        port: int = 22,
        timeout: int = 300,
        **kwargs,
    ):
        super().__init__(task_id, name, **kwargs)
        self.host = host
        self.command = command
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.timeout = timeout

    async def execute(self) -> TaskResult:
        try:
            # 创建SSH客户端
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 连接服务器
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                key_filename=self.key_filename,
                timeout=self.timeout,
            )

            # 执行命令
            stdin, stdout, stderr = client.exec_command(self.command)

            # 获取结果
            stdout_data = stdout.read().decode()
            stderr_data = stderr.read().decode()
            exit_code = stdout.channel.recv_exit_status()

            # 关闭连接
            client.close()

            if exit_code == 0:
                return TaskResult(
                    success=True,
                    message="Command executed successfully",
                    data={"stdout": stdout_data, "stderr": stderr_data},
                )
            else:
                return TaskResult(
                    success=False,
                    message=f"Command failed with exit code {exit_code}",
                    data={"stdout": stdout_data, "stderr": stderr_data},
                )

        except Exception as e:
            self.error = e
            return TaskResult(success=False, message=str(e), error=e)


class PythonTask(Task):
    """Python函数任务"""

    def __init__(
        self,
        task_id: str,
        name: str,
        func: Callable,
        args: tuple = None,
        kwargs: dict = None,
        **task_kwargs,
    ):
        super().__init__(task_id, name, **task_kwargs)
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}

    async def execute(self) -> TaskResult:
        try:
            # 执行函数
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(*self.args, **self.kwargs)
            else:
                result = self.func(*self.args, **self.kwargs)

            return TaskResult(
                success=True, message="Function executed successfully", data=result
            )

        except Exception as e:
            self.error = e
            return TaskResult(success=False, message=str(e), error=e)


class TaskScheduler:
    """任务调度器"""

    def __init__(self, max_workers: int = None):
        self.tasks: Dict[str, Task] = {}
        self.scheduled_tasks: Dict[str, schedule.Job] = {}
        self.task_queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False

    def add_task(self, task: Task):
        """添加任务"""
        self.tasks[task.task_id] = task
        self.task_queue.put(task)

    def schedule_task(self, task: Task, trigger: str, **schedule_kwargs):
        """调度任务"""
        job = None

        # 创建调度作业
        if trigger == "interval":
            interval = schedule_kwargs.get("interval")
            if isinstance(interval, (int, float)):
                job = schedule.every(interval).seconds
            elif isinstance(interval, timedelta):
                job = schedule.every(interval.total_seconds()).seconds

        elif trigger == "cron":
            job = schedule.every()

            # 设置cron表达式
            if "day_of_week" in schedule_kwargs:
                job = job.day_of_week(schedule_kwargs["day_of_week"])
            if "hour" in schedule_kwargs:
                job = job.at(f"{schedule_kwargs['hour']:02d}:00")
            if "minute" in schedule_kwargs:
                job = job.at(f"00:{schedule_kwargs['minute']:02d}")

        if job:
            # 添加任务
            job.do(lambda: self.add_task(task))
            self.scheduled_tasks[task.task_id] = job

    async def execute_task(self, task: Task):
        """执行任务"""
        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()

            # 执行任务
            result = await task.execute()

            # 如果失败且需要重试
            if not result.success and task.retry_count > 0:
                result = await task.retry()

            # 更新任务状态和结果
            task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            task.result = result

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = e

        finally:
            task.end_time = datetime.now()

    async def process_tasks(self):
        """处理任务队列"""
        while self.running:
            try:
                # 获取任务
                task = self.task_queue.get_nowait()

                # 执行任务
                await self.execute_task(task)

                # 标记任务完成
                self.task_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task processing error: {e}")

            # 短暂休息
            await asyncio.sleep(0.1)

    def run_scheduler(self):
        """运行调度器"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    async def start(self):
        """启动调度器"""
        self.running = True

        # 启动调度线程
        schedule_thread = threading.Thread(target=self.run_scheduler)
        schedule_thread.daemon = True
        schedule_thread.start()

        # 启动任务处理
        await self.process_tasks()

    async def stop(self):
        """停止调度器"""
        self.running = False

        # 等待所有任务完成
        await self.task_queue.join()

        # 清理资源
        self.executor.shutdown(wait=True)


class AutomationManager:
    """自动化管理器"""

    def __init__(self, max_workers: int = None):
        self.scheduler = TaskScheduler(max_workers=max_workers)
        self.task_templates: Dict[str, Dict] = {}

    def register_template(self, template_id: str, task_type: str, template: Dict):
        """注册任务模板"""
        self.task_templates[template_id] = {"type": task_type, "template": template}

    def create_task_from_template(
        self, template_id: str, task_id: str, name: str, params: Dict = None
    ) -> Optional[Task]:
        """从模板创建任务"""
        try:
            template_info = self.task_templates.get(template_id)
            if not template_info:
                raise ValueError(f"Template {template_id} not found")

            # 合并参数
            task_params = {**template_info["template"], **(params or {})}

            # 创建任务
            task_type = template_info["type"]
            if task_type == "http":
                return HttpTask(task_id, name, **task_params)
            elif task_type == "shell":
                return ShellTask(task_id, name, **task_params)
            elif task_type == "ssh":
                return SSHTask(task_id, name, **task_params)
            elif task_type == "python":
                return PythonTask(task_id, name, **task_params)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

        except Exception as e:
            logger.error(f"Failed to create task from template: {e}")
            return None

    async def start(self):
        """启动自动化管理器"""
        await self.scheduler.start()

    async def stop(self):
        """停止自动化管理器"""
        await self.scheduler.stop()

    def add_task(self, task: Task):
        """添加任务"""
        self.scheduler.add_task(task)

    def schedule_task(self, task: Task, trigger: str, **schedule_kwargs):
        """调度任务"""
        self.scheduler.schedule_task(task, trigger, **schedule_kwargs)

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获��任务状态"""
        task = self.scheduler.tasks.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status.value,
            "start_time": task.start_time,
            "end_time": task.end_time,
            "result": task.result.__dict__ if task.result else None,
            "error": str(task.error) if task.error else None,
        }

    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务"""
        return [
            self.get_task_status(task_id) for task_id in self.scheduler.tasks.keys()
        ]
