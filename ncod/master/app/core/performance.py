"""
性能优化模块
"""

import asyncio
import concurrent.futures
import functools
import time
from multiprocessing import Process
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    Generic,
    List,
    NamedTuple,
    Optional,
    ParamSpec,
    Protocol,
    Set,
    Type,
    TypeAlias,
    TypeGuard,
    TypeVar,
    Union,
    cast,
    overload,
)

from app.core.config import settings
from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool

T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")

AsyncResult: TypeAlias = Awaitable[R] | Coroutine[Any, Any, R]


class TimeMetric(NamedTuple):
    """时间指标"""

    start_time: float
    end_time: float
    duration: float


class AsyncCallable(Protocol[P, R]):
    """异步可调用对象协议"""

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> AsyncResult[R]: ...

    __name__: str


class SyncCallable(Protocol[P, R]):
    """同步可调用对象协议"""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

    __name__: str


def is_async_callable(obj: Any) -> TypeGuard[AsyncCallable[Any, Any]]:
    """检查是否为异步可调用对象"""
    return hasattr(obj, "__call__") and asyncio.iscoroutinefunction(obj.__call__)


def is_sync_callable(obj: Any) -> TypeGuard[SyncCallable[Any, Any]]:
    """检查是否为同步可调用对象"""
    return hasattr(obj, "__call__") and not asyncio.iscoroutinefunction(obj.__call__)


@overload
def timed(func: AsyncCallable[P, R]) -> AsyncCallable[P, R]: ...


@overload
def timed(func: SyncCallable[P, R]) -> SyncCallable[P, R]: ...


def timed(
    func: Union[AsyncCallable[P, R], SyncCallable[P, R]]
) -> Union[AsyncCallable[P, R], SyncCallable[P, R]]:
    """通用计时装饰器"""
    if is_async_callable(func):

        @functools.wraps(func)
        async def async_wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                if isinstance(result, (Awaitable, Coroutine)):
                    result = await result
                return cast(R, result)
            finally:
                end = time.time()
                total = end - start
                print(f"{func.__name__} took {total:.2f} seconds")

        return cast(AsyncCallable[P, R], async_wrapped)
    else:

        @functools.wraps(func)
        def sync_wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                end = time.time()
                total = end - start
                print(f"{func.__name__} took {total:.2f} seconds")

        return cast(SyncCallable[P, R], sync_wrapped)


class ProcessInfo(Generic[T]):
    """进程信息"""

    def __init__(self, process: Process, start_time: float):
        self.process = process
        self.start_time = start_time


class ProcessManager:
    """进程管理器"""

    def __init__(self):
        self.processes: Dict[str, ProcessInfo[Any]] = {}

    def start_process(
        self, name: str, target: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> None:
        """启动进程"""
        process = Process(target=target, args=args, kwargs=kwargs)
        process.start()
        self.processes[name] = ProcessInfo(process, time.time())

    def stop_process(self, name: str) -> None:
        """停止进程"""
        if name in self.processes:
            info = self.processes[name]
            info.process.terminate()
            info.process.join()
            del self.processes[name]

    def get_process_info(self, name: str) -> Optional[ProcessInfo[Any]]:
        """获取进程信息"""
        return self.processes.get(name)

    def cleanup(self) -> None:
        """清理所有进程"""
        for name in list(self.processes.keys()):
            self.stop_process(name)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics: Dict[str, List[TimeMetric]] = {}

    def record_time(self, name: str, start_time: float, end_time: float) -> None:
        """记录时间指标"""
        duration = end_time - start_time
        metric = TimeMetric(start_time, end_time, duration)

        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(metric)

    def get_metrics(self, name: str) -> List[TimeMetric]:
        """获取指标"""
        return self.metrics.get(name, [])

    def clear_metrics(self, name: str) -> None:
        """清除指标"""
        if name in self.metrics:
            del self.metrics[name]


class RateLimiter:
    """速率限制器"""

    def __init__(self, rate: int, period: int = 60):
        self.rate = rate  # 请求次数
        self.period = period  # 时间周期（秒）
        self.tokens: Dict[str, Dict[str, Union[int, float]]] = {}  # 令牌桶
        self._lock = asyncio.Lock()

    async def acquire(self, key: str) -> bool:
        """获取令牌"""
        async with self._lock:
            now = time.time()

            # 初始化或更新令牌桶
            if key not in self.tokens:
                self.tokens[key] = {"tokens": self.rate, "last_update": now}
            else:
                # 计算需要补充的令牌数
                elapsed = now - self.tokens[key]["last_update"]
                tokens_to_add = int(elapsed * self.rate / self.period)

                if tokens_to_add > 0:
                    self.tokens[key]["tokens"] = min(
                        self.rate, self.tokens[key]["tokens"] + tokens_to_add
                    )
                    self.tokens[key]["last_update"] = now

            # 检查是否有可用令牌
            if self.tokens[key]["tokens"] > 0:
                self.tokens[key]["tokens"] -= 1
                return True

            return False

    def rate_limit(self, rate: int, period: int = 60):
        """速率限制装饰器"""

        def decorator(func):
            limiter = RateLimiter(rate, period)

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # 获取请求对象
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

                if request is None:
                    raise ValueError("No request object found")

                # 使用客户端IP作为限制键
                client = request.client
                if client is None:
                    raise ValueError("No client information found")

                key = client.host or "unknown"

                # 尝试获取令牌
                if not await limiter.acquire(key):
                    raise HTTPException(status_code=429, detail="Too many requests")

                return await func(*args, **kwargs)

            return wrapper

        return decorator


class BatchProcessor:
    """批处理器"""

    def __init__(self, batch_size: int = 100, max_wait: float = 1.0):
        self.batch_size = batch_size
        self.max_wait = max_wait
        self.items = []
        self.last_process_time = time.time()
        self._lock = asyncio.Lock()

    async def add(self, item: Any) -> None:
        """添加项目"""
        async with self._lock:
            self.items.append(item)

            # 检查是否需要处理
            now = time.time()
            if (
                len(self.items) >= self.batch_size
                or now - self.last_process_time >= self.max_wait
            ):
                await self.process()

    async def process(self) -> None:
        """处理项目"""
        async with self._lock:
            if not self.items:
                return

            # 处理项目的具体逻辑
            # 这里需要根据实际需求实现

            # 清空项目列表
            self.items = []
            self.last_process_time = time.time()


class AsyncPool:
    """异步任务池"""

    def __init__(self, max_workers: int = settings.PERFORMANCE_MAX_WORKERS):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        self.tasks = set()

    async def run(self, coro):
        """运行协程"""
        async with self.semaphore:
            task = asyncio.create_task(coro)
            self.tasks.add(task)
            try:
                return await task
            finally:
                self.tasks.remove(task)

    async def join(self):
        """等待所有任务完成"""
        if self.tasks:
            await asyncio.gather(*self.tasks)


class ThreadPoolExecutorManager:
    """线程池管理器"""

    def __init__(self, max_workers: int = settings.PERFORMANCE_THREAD_POOL_SIZE):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def run(self, func: Callable, *args, **kwargs) -> Any:
        """在线程池中运行函数"""
        return await run_in_threadpool(func, *args, **kwargs)

    def shutdown(self):
        """关闭线程池"""
        self.executor.shutdown()


class ProcessPoolExecutorManager:
    """进程池管理器"""

    def __init__(self, max_workers: int = settings.PERFORMANCE_PROCESS_POOL_SIZE):
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)

    async def run(self, func: Callable, *args, **kwargs) -> Any:
        """在进程池中运行函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, functools.partial(func, *args, **kwargs)
        )

    def shutdown(self):
        """关闭进程池"""
        self.executor.shutdown()


class TimeoutManager:
    """超时管理器"""

    @staticmethod
    async def run_with_timeout(
        coro, timeout: float = settings.PERFORMANCE_TIMEOUT
    ) -> Any:
        """运行带超时的协程"""
        try:
            return await asyncio.wait_for(coro, timeout)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Request timeout")


def async_timed() -> Callable[[AsyncCallable[P, T]], AsyncCallable[P, T]]:
    """异步函数计时装饰器"""

    def wrapper(func: AsyncCallable[P, T]) -> AsyncCallable[P, T]:
        @functools.wraps(func)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                end = time.time()
                total = end - start
                print(f"{func.__name__} took {total:.2f} seconds")

        return cast(AsyncCallable[P, T], wrapped)

    return wrapper


def sync_timed() -> Callable[[SyncCallable[P, T]], SyncCallable[P, T]]:
    """同步函数计时装饰器"""

    def wrapper(func: SyncCallable[P, T]) -> SyncCallable[P, T]:
        @functools.wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                end = time.time()
                total = end - start
                print(f"{func.__name__} took {total:.2f} seconds")

        return cast(SyncCallable[P, T], wrapped)

    return wrapper


class PerformanceMiddleware:
    """性能中间件"""

    async def __call__(self, request: Request, call_next):
        # 记录开始时间
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 添加处理时间响应头
        response.headers["X-Process-Time"] = str(process_time)

        return response
