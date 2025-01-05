import threading
from typing import Dict, Callable, Optional, List
from datetime import datetime, timedelta
from .utils.logger import get_logger

logger = get_logger(__name__)


class Task:
    def __init__(
        self,
        func: Callable,
        interval: int,
        name: str,
        args: tuple = (),
        kwargs: dict = None
    ) -> None:
        self.func = func
        self.interval = interval
        self.name = name
        self.args = args
        self.kwargs = kwargs or {}
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
    
    def should_run(self) -> bool:
        """检查是否应该运行任务"""
        if not self.next_run:
            return True
        return datetime.utcnow() >= self.next_run
    
    def update_schedule(self) -> None:
        """更新任务计划时间"""
        self.last_run = datetime.utcnow()
        self.next_run = self.last_run + timedelta(seconds=self.interval)


class SchedulerManager:
    _instance: Optional['SchedulerManager'] = None
    _tasks: Dict[str, Task] = {}
    _running = False
    _thread: Optional[threading.Thread] = None
    
    def __new__(cls) -> 'SchedulerManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if not self._thread:
            self._thread = threading.Thread(target=self._run, daemon=True)
    
    def start(self) -> None:
        """启动调度器"""
        if not self._running:
            self._running = True
            self._thread.start()
            logger.info("Scheduler started")
    
    def stop(self) -> None:
        """停止调度器"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join()
            logger.info("Scheduler stopped")
    
    def add_task(
        self,
        func: Callable,
        interval: int,
        name: str,
        args: tuple = (),
        kwargs: dict = None
    ) -> bool:
        """添加任务"""
        try:
            if name in self._tasks:
                logger.warning(f"Task {name} already exists")
                return False
                
            task = Task(func, interval, name, args, kwargs)
            self._tasks[name] = task
            logger.info(f"Task {name} added")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add task {name}: {e}")
            return False
    
    def remove_task(self, name: str) -> bool:
        """移除任务"""
        try:
            if name not in self._tasks:
                logger.warning(f"Task {name} not found")
                return False
                
            task = self._tasks[name]
            if task.is_running:
                logger.warning(f"Task {name} is running")
                return False
                
            del self._tasks[name]
            logger.info(f"Task {name} removed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove task {name}: {e}")
            return False
    
    def get_task(self, name: str) -> Optional[Dict]:
        """获取任务信息"""
        try:
            task = self._tasks.get(name)
            if not task:
                return None
                
            return {
                'name': task.name,
                'interval': task.interval,
                'last_run': (
                    task.last_run.isoformat()
                    if task.last_run else None
                ),
                'next_run': (
                    task.next_run.isoformat()
                    if task.next_run else None
                ),
                'is_running': task.is_running
            }
            
        except Exception as e:
            logger.error(f"Failed to get task {name}: {e}")
            return None
    
    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务信息"""
        try:
            tasks = []
            for name, task in self._tasks.items():
                tasks.append({
                    'name': task.name,
                    'interval': task.interval,
                    'last_run': (
                        task.last_run.isoformat()
                        if task.last_run else None
                    ),
                    'next_run': (
                        task.next_run.isoformat()
                        if task.next_run else None
                    ),
                    'is_running': task.is_running
                })
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get all tasks: {e}")
            return []
    
    def _run(self) -> None:
        """运行调度器主循环"""
        while self._running:
            try:
                for name, task in self._tasks.items():
                    if task.should_run() and not task.is_running:
                        task.is_running = True
                        task.thread = threading.Thread(
                            target=self._execute_task,
                            args=(task,)
                        )
                        task.thread.start()
                        
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                
            # 休眠1秒
            threading.Event().wait(1)
    
    def _execute_task(self, task: Task) -> None:
        """执行任务"""
        try:
            task.func(*task.args, **task.kwargs)
            task.update_schedule()
            
        except Exception as e:
            logger.error(f"Task {task.name} execution failed: {e}")
            
        finally:
            task.is_running = False
            task.thread = None 