"""
Adam Prism — Task Queue
========================
طابور مهام بسيط في الذاكرة مع أولويات وتتبع.
بديل خفيف عن Redis/RabbitMQ — مناسب للاستخدام الفردي والخوادم الصغيرة.

Features:
- Priority-based task scheduling
- Task deduplication by key
- Retry with exponential backoff
- Task result caching
- Concurrency limits
"""

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum
from typing import Any

logger = logging.getLogger("adam_prism.orchestrator.task_queue")

class TaskStatus(str):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3

@dataclass
class Task:
    """مهمة في الطابور"""
    name: str
    handler: Callable
    args: tuple = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    dedup_key: str | None = None
    max_retries: int = 2
    retry_count: int = 0
    status: str = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    timeout: float = 300.0  # 5 minutes default

    def __lt__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return self.priority < other.priority

class TaskQueue:
    """
    طابور مهام غير متزامن مع إدارة كاملة

    Usage:
        queue = TaskQueue(max_concurrent=3)

        async def process_data(data):
            return f"processed: {data}"

        # Add task
        task = await queue.enqueue(
            name="process_data",
            handler=process_data,
            args=("hello",),
            priority=TaskPriority.HIGH
        )

        # Wait for result
        result = await queue.wait_for(task.task_id)
    """

    def __init__(self, max_concurrent: int = 3):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: dict[str, Task] = {}
        self._dedup_keys: set[str] = set()
        self._max_concurrent = max_concurrent
        self._running_count = 0
        self._worker_tasks: list[asyncio.Task] = []
        self._running = False
        self._results_cache: dict[str, Any] = {}
        self._results_ttl: dict[str, float] = {}
        self._lock = asyncio.Lock()
        # Stats
        self._total_enqueued = 0
        self._total_completed = 0
        self._total_failed = 0

    async def start(self, num_workers: int | None = None):
        """تشغيل عمال الطابور"""
        if self._running:
            return
        self._running = True
        workers = num_workers or self._max_concurrent
        for i in range(workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self._worker_tasks.append(worker)
        logger.info(f"TaskQueue: {workers} workers started")

    async def stop(self):
        """إيقاف الطابور"""
        self._running = False
        for task in self._worker_tasks:
            task.cancel()
        self._worker_tasks.clear()
        logger.info("TaskQueue: stopped")

    async def enqueue(
        self,
        name: str,
        handler: Callable,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        dedup_key: str | None = None,
        max_retries: int = 2,
        timeout: float = 300.0,
    ) -> Task:
        """
        إضافة مهمة للطابور
        - dedup_key: لو موجود، لا يُضاف مهمة بنفس المفتاح مرتين
        """
        async with self._lock:
            # Deduplication check
            if dedup_key and dedup_key in self._dedup_keys:
                # Find existing task
                for t in self._tasks.values():
                    if t.dedup_key == dedup_key and t.status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING):
                        logger.info(f"TaskQueue: dedup skip '{name}' (key={dedup_key})")
                        return t

            task = Task(
                name=name,
                handler=handler,
                args=args,
                kwargs=kwargs or {},
                priority=priority,
                dedup_key=dedup_key,
                max_retries=max_retries,
                timeout=timeout,
            )
            self._tasks[task.task_id] = task
            if dedup_key:
                self._dedup_keys.add(dedup_key)
            await self._queue.put(task)
            self._total_enqueued += 1
            logger.debug(f"TaskQueue: enqueued '{name}' (id={task.task_id}, priority={priority.name})")
            return task

    async def wait_for(self, task_id: str, timeout: float = 60.0) -> Any:
        """انتظار نتيجة مهمة"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            task = self._tasks.get(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            if task.status == TaskStatus.COMPLETED:
                return task.result
            if task.status == TaskStatus.FAILED:
                raise RuntimeError(f"Task failed: {task.error}")
            if task.status == TaskStatus.CANCELLED:
                raise RuntimeError("Task was cancelled")
            await asyncio.sleep(0.1)
        raise TimeoutError(f"Task {task_id} did not complete in {timeout}s")

    async def cancel(self, task_id: str) -> bool:
        """إلغاء مهمة"""
        task = self._tasks.get(task_id)
        if not task:
            return False
        if task.status in (TaskStatus.PENDING, TaskStatus.RETRYING):
            task.status = TaskStatus.CANCELLED
            if task.dedup_key:
                self._dedup_keys.discard(task.dedup_key)
            return True
        return False

    async def _worker_loop(self, worker_id: int):
        """دورة عمل لتنفيذ المهام"""
        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            if task.status == TaskStatus.CANCELLED:
                self._queue.task_done()
                continue

            # Concurrency check
            if self._running_count >= self._max_concurrent:
                # Re-enqueue
                await self._queue.put(task)
                await asyncio.sleep(0.5)
                continue

            self._running_count += 1
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(UTC).isoformat()

            try:
                result = await asyncio.wait_for(
                    task.handler(*task.args, **task.kwargs),
                    timeout=task.timeout,
                )
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(UTC).isoformat()
                self._total_completed += 1
                # Cache result
                self._results_cache[task.task_id] = result
                self._results_ttl[task.task_id] = time.time() + 300  # 5 min cache
            except TimeoutError:
                task.error = f"Task timed out after {task.timeout}s"
                await self._handle_failure(task)
            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
            except Exception as e:
                task.error = str(e)
                await self._handle_failure(task)
            finally:
                self._running_count -= 1
                self._queue.task_done()
                if task.dedup_key and task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    self._dedup_keys.discard(task.dedup_key)

    async def _handle_failure(self, task: Task):
        """معالجة تعذر المهمة — إعادة محاولة أو وضع فاشل"""
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.RETRYING
            delay = min(0.5 * (2 ** task.retry_count), 30.0)
            logger.warning(
                f"TaskQueue: retry '{task.name}' (attempt {task.retry_count}/{task.max_retries}) in {delay:.1f}s"
            )
            await asyncio.sleep(delay)
            await self._queue.put(task)
        else:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now(UTC).isoformat()
            self._total_failed += 1
            logger.error(f"TaskQueue: '{task.name}' failed permanently: {task.error}")

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """معلومات مهمة"""
        task = self._tasks.get(task_id)
        if not task:
            return None
        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status,
            "priority": task.priority.name,
            "retry_count": task.retry_count,
            "error": task.error,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
        }

    def list_tasks(self, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """قائمة المهام"""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return [
            {
                "task_id": t.task_id,
                "name": t.name,
                "status": t.status,
                "priority": t.priority.name,
                "created_at": t.created_at,
            }
            for t in tasks[:limit]
        ]

    def cleanup(self, max_age_hours: int = 24):
        """تنظيف المهام القديمة"""
        now = datetime.now(UTC)
        cutoff = now.timestamp() - (max_age_hours * 3600)
        to_remove = []
        for task_id, task in self._tasks.items():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                if task.completed_at:
                    try:
                        completed_ts = datetime.fromisoformat(task.completed_at).timestamp()
                        if completed_ts < cutoff:
                            to_remove.append(task_id)
                    except (ValueError, TypeError):
                        pass
        for task_id in to_remove:
            self._tasks.pop(task_id, None)
            self._results_cache.pop(task_id, None)
            self._results_ttl.pop(task_id, None)
        # Clean expired result cache
        now_ts = time.time()
        expired = [k for k, v in self._results_ttl.items() if v < now_ts]
        for k in expired:
            self._results_cache.pop(k, None)
            self._results_ttl.pop(k, None)
        if to_remove or expired:
            logger.info(f"TaskQueue: cleaned up {len(to_remove)} old tasks, {len(expired)} expired cache entries")

    def stats(self) -> dict[str, Any]:
        return {
            "total_enqueued": self._total_enqueued,
            "total_completed": self._total_completed,
            "total_failed": self._total_failed,
            "queue_size": self._queue.qsize(),
            "running_count": self._running_count,
            "max_concurrent": self._max_concurrent,
            "tasks_tracked": len(self._tasks),
            "dedup_keys_active": len(self._dedup_keys),
            "results_cached": len(self._results_cache),
        }
