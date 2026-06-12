"""
Adam Prism — Async Task Queue
================================
طابور مهام غير متزامن مع أولويات وإلغاء مكرر وتراجع أسّي.

A priority-based task queue with deduplication, exponential backoff retry,
concurrency limits, and automatic cleanup.

المميزات / Features:
  - أولويات المهام (CRITICAL → BACKGROUND) — Task priorities
  - إلغاء المكرر — Deduplication (skip if same-named task is PENDING/RUNNING)
  - تراجع أسّي عند الفشل — Exponential backoff on retry
  - حد أقصى للمهام المتزامنة — Max concurrent tasks limit
  - تنظيف تلقائي للمهام القديمة — Automatic cleanup of old tasks
  - تجمع عمال — Worker pool for processing
  - إحصائيات شاملة — Comprehensive statistics
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger("adam_prism.orchestrator.task_queue")


# ═══════════════════════════════════════════════════════════════
# أنماط البيانات / Data Models
# ═══════════════════════════════════════════════════════════════

class TaskStatus(str):
    """
    حالة المهمة — Task status.
    """
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(IntEnum):
    """
    أولوية المهمة — كلما زادت القيمة، زادت الأولوية.
    Task priority — higher value = higher priority.
    """
    BACKGROUND = 0
    LOW = 5
    NORMAL = 10
    HIGH = 15
    CRITICAL = 20


@dataclass
class Task:
    """
    مهمة في الطابور — A task in the queue.

    Attributes / الخصائص:
        id: معرف فريد للمهمة — Unique task identifier
        name: اسم المهمة (يُستخدم للإلغاء المكرر) — Task name (used for dedup)
        func: الدالة المراد تنفيذها — Callable to execute
        args: المعاملات الموضعية — Positional arguments
        kwargs: المعاملات المسماة — Keyword arguments
        priority: الأولوية — Task priority
        status: الحالة الحالية — Current status
        created_at: وقت الإنشاء — Creation timestamp
        started_at: وقت بدء التنفيذ — Execution start timestamp
        completed_at: وقت الانتهاء — Completion timestamp
        result: النتيجة — Task result
        error: رسالة الخطأ — Error message if failed
        retries: عدد المحاولات — Current retry count
        max_retries: الحد الأقصى للمحاولات — Max retry attempts
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    func: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: str = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3


# ═══════════════════════════════════════════════════════════════
# طابور المهام / Task Queue
# ═══════════════════════════════════════════════════════════════

class TaskQueue:
    """
    طابور مهام غير متزامن مع أولويات — Async priority task queue.

    الاستخدام الأساسي / Basic Usage:
        queue = TaskQueue(max_concurrent=5)
        await queue.start()
        task = await queue.enqueue("fetch_data", fetch_data_fn, args=[url])
        await queue.stop()

    المميزات / Features:
      - ترتيب حسب الأولوية — Priority-based dequeue
      - إلغاء المكرر — Deduplication by task name
      - تراجع أسّي — Exponential backoff retry
      - حد التزامن — Max concurrent tasks limit
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        worker_count: int = 3,
        default_max_retries: int = 3,
    ) -> None:
        """
        تهيئة طابور المهام — Initialize the task queue.

        Args / المعاملات:
            max_concurrent: الحد الأقصى للمهام المتزامنة — Max concurrent running tasks
            worker_count: عدد العمال — Number of worker coroutines
            default_max_retries: المحاولات الافتراضية — Default max retries per task
        """
        self._tasks: Dict[str, Task] = {}
        self._pending_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._max_concurrent = max_concurrent
        self._worker_count = worker_count
        self._default_max_retries = default_max_retries
        self._running = False
        self._workers: List[asyncio.Task] = []

        # عدّاد المهام المتزامنة — Concurrency counter
        self._running_count = 0
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # إشعار بوجود مهام جديدة — Notification for new tasks
        self._task_available = asyncio.Event()

        # قفل لسلامة العمليات — Lock for shared state
        self._lock = asyncio.Lock()

    # ─────────────────────────────────────────────
    # إدارة المهام / Task Management
    # ─────────────────────────────────────────────

    async def enqueue(
        self,
        name: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: Optional[int] = None,
    ) -> Task:
        """
        إضافة مهمة إلى الطابور — Enqueue a new task.

        Args / المعاملات:
            name: اسم المهمة (يُستخدم للإلغاء المكرر) — Task name (dedup key)
            func: الدالة async المراد تنفيذها — Async function to execute
            args: المعاملات الموضعية — Positional arguments
            kwargs: المعاملات المسماة — Keyword arguments
            priority: الأولوية — Task priority
            max_retries: الحد الأقصى للمحاولات — Max retry attempts (None = default)

        Returns / المخرجات:
            المهمة المنشأة — The created Task

        Raises / الاستثناءات:
            ValueError: إذا كانت هناك مهمة بنفس الاسم قيد التنفيذ أو الانتظار
                        — If a task with the same name is already PENDING/RUNNING
        """
        # فحص الإلغاء المكرر — Deduplication check
        async with self._lock:
            for existing in self._tasks.values():
                if existing.name == name and existing.status in (
                    TaskStatus.PENDING, TaskStatus.RUNNING
                ):
                    logger.info(
                        "Dedup: task '%s' already %s (id=%s)",
                        name, existing.status, existing.id[:8],
                    )
                    return existing

        task = Task(
            name=name,
            func=func,
            args=args or [],
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries if max_retries is not None else self._default_max_retries,
        )

        async with self._lock:
            self._tasks[task.id] = task

        # إضافة إلى طابور الأولوية — Enqueue with priority
        # (سالب لأن PriorityQueue ترتب تصاعدياً ونريد أعلى أولوية أولاً)
        await self._pending_queue.put((-priority, task.created_at, task.id))

        # إيقاظ العمال — Wake up workers
        self._task_available.set()

        logger.info(
            "Enqueued task '%s' [%s] priority=%s",
            name, task.id[:8], priority.name,
        )
        return task

    async def dequeue(self) -> Optional[Task]:
        """
        استخراج المهمة ذات الأولوية القصوى — Dequeue the highest-priority task.

        Returns / المخرجات:
            المهمة التالية أو None إذا كان الطابور فارغاً — Next task or None
        """
        try:
            neg_priority, ts, task_id = self._pending_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

        async with self._lock:
            task = self._tasks.get(task_id)
        if task is None or task.status != TaskStatus.PENDING:
            return await self.dequeue()  # تجاهل المهام الملغاة — Skip cancelled

        return task

    async def mark_completed(self, task_id: str, result: Any = None) -> bool:
        """
        تحديد مهمة كمكتملة — Mark a task as completed.

        Args / المعاملات:
            task_id: معرف المهمة — Task ID
            result: النتيجة — Task result

        Returns / المخرجات:
            True إذا تم التحديث، False إذا لم تُوجَد — True if updated
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return False
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = time.time()

        logger.info("Task '%s' [%s] completed", task.name, task_id[:8])
        return True

    async def mark_failed(self, task_id: str, error: str) -> bool:
        """
        تحديد مهمة كفاشلة — Mark a task as failed.

        Args / المعاملات:
            task_id: معرف المهمة — Task ID
            error: رسالة الخطأ — Error message

        Returns / المخرجات:
            True إذا تم التحديث — True if updated
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return False
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = time.time()

        logger.warning("Task '%s' [%s] failed: %s", task.name, task_id[:8], error[:200])
        return True

    async def retry_task(self, task_id: str) -> bool:
        """
        إعادة محاولة مهمة فاشلة مع تراجع أسّي — Retry a failed task with exponential backoff.

        Args / المعاملات:
            task_id: معرف المهمة — Task ID

        Returns / المخرجات:
            True إذا تمت جدولة الإعادة، False إذا تعذّرت — True if retry scheduled
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return False
            if task.status != TaskStatus.FAILED:
                return False
            if task.retries >= task.max_retries:
                logger.warning(
                    "Task '%s' [%s] exhausted retries (%d/%d)",
                    task.name, task_id[:8], task.retries, task.max_retries,
                )
                return False

        # تراجع أسّي: 2^retries ثانية — Exponential backoff: 2^retries seconds
        backoff = min(2 ** task.retries, 60)  # حد أقصى 60 ثانية — Cap at 60s

        async with self._lock:
            task.retries += 1
            task.status = TaskStatus.PENDING
            task.error = None
            task.completed_at = None
            task.started_at = None

        # انتظار التراجع — Wait for backoff
        await asyncio.sleep(backoff)

        # إعادة إضافة إلى الطابور — Re-enqueue
        await self._pending_queue.put((-task.priority, time.time(), task.id))
        self._task_available.set()

        logger.info(
            "Retrying task '%s' [%s] (attempt %d/%d, backoff=%ds)",
            task.name, task_id[:8], task.retries, task.max_retries, backoff,
        )
        return True

    async def cancel(self, task_id: str) -> bool:
        """
        إلغاء مهمة — Cancel a pending or running task.

        Args / المعاملات:
            task_id: معرف المهمة — Task ID

        Returns / المخرجات:
            True إذا تم الإلغاء — True if cancelled
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return False
            if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
                return False
            task.status = TaskStatus.CANCELLED
            task.completed_at = time.time()

        logger.info("Task '%s' [%s] cancelled", task.name, task_id[:8])
        return True

    # ─────────────────────────────────────────────
    # التنظيف / Cleanup
    # ─────────────────────────────────────────────

    async def cleanup(self, max_age_seconds: int = 3600) -> int:
        """
        إزالة المهام القديمة المكتملة أو الفاشلة — Remove old completed/failed tasks.

        Args / المعاملات:
            max_age_seconds: العمر الأقصى بالثواني — Max age in seconds

        Returns / المخرجات:
            عدد المهام المحذوفة — Number of tasks removed
        """
        cutoff = time.time() - max_age_seconds
        removed = 0

        async with self._lock:
            to_remove = [
                tid for tid, t in self._tasks.items()
                if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
                and t.completed_at is not None
                and t.completed_at < cutoff
            ]
            for tid in to_remove:
                del self._tasks[tid]
                removed += 1

        if removed:
            logger.info("Cleaned up %d old tasks (max_age=%ds)", removed, max_age_seconds)
        return removed

    # ─────────────────────────────────────────────
    # تجمع العمال / Worker Pool
    # ─────────────────────────────────────────────

    async def start(self) -> None:
        """
        بدء تجمع العمال — Start the task processing worker pool.
        """
        if self._running:
            logger.warning("TaskQueue already running — ignoring start()")
            return

        self._running = True
        for i in range(self._worker_count):
            task = asyncio.create_task(self._worker_loop(i), name=f"taskqueue-worker-{i}")
            self._workers.append(task)

        logger.info("TaskQueue started with %d workers (max_concurrent=%d)", self._worker_count, self._max_concurrent)

    async def _worker_loop(self, worker_id: int) -> None:
        """
        حلقة العامل — Worker loop that processes tasks from the queue.
        """
        while self._running:
            try:
                # انتظار مهمة — Wait for a task
                try:
                    await asyncio.wait_for(self._task_available.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                task = await self.dequeue()
                if task is None:
                    self._task_available.clear()
                    continue

                # التحقق من حد التزامن — Check concurrency limit
                await self._semaphore.acquire()
                try:
                    async with self._lock:
                        self._running_count += 1

                    task.status = TaskStatus.RUNNING
                    task.started_at = time.time()

                    if task.func is None:
                        raise ValueError(f"Task '{task.name}' has no function to execute")

                    result = await asyncio.wait_for(
                        task.func(*task.args, **task.kwargs),
                        timeout=300.0,  # حد أقصى 5 دقائق — 5 min timeout
                    )
                    await self.mark_completed(task.id, result)

                except asyncio.TimeoutError:
                    await self.mark_failed(task.id, "Task timed out (300s)")
                    # محاولة إعادة تلقائية — Auto-retry
                    if task.retries < task.max_retries:
                        await self.retry_task(task.id)

                except asyncio.CancelledError:
                    await self.cancel(task.id)
                    break

                except Exception as exc:
                    await self.mark_failed(task.id, str(exc))
                    # محاولة إعادة تلقائية — Auto-retry
                    if task.retries < task.max_retries:
                        await self.retry_task(task.id)

                finally:
                    async with self._lock:
                        self._running_count -= 1
                    self._semaphore.release()

                    # إيقاظ العمال الآخرين — Wake other workers
                    self._task_available.set()

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Worker %d unexpected error: %s", worker_id, exc, exc_info=True)

    # ─────────────────────────────────────────────
    # الإحصائيات / Statistics
    # ─────────────────────────────────────────────

    async def get_stats(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات الطابور — Get queue statistics.

        Returns / المخرجات:
            قاموس يحتوي على:
            - total_tasks: إجمالي المهام
            - pending: عدد المهام في الانتظار
            - running: عدد المهام قيد التنفيذ
            - completed: عدد المهام المكتملة
            - failed: عدد المهام الفاشلة
            - cancelled: عدد المهام الملغاة
            - max_concurrent: الحد الأقصى للتزامن
            - workers_active: عدد العمال النشطين
        """
        async with self._lock:
            counts = {
                "PENDING": 0, "RUNNING": 0, "COMPLETED": 0,
                "FAILED": 0, "CANCELLED": 0,
            }
            for t in self._tasks.values():
                counts[t.status] = counts.get(t.status, 0) + 1

            return {
                "total_tasks": len(self._tasks),
                "pending": counts["PENDING"],
                "running": counts["RUNNING"],
                "completed": counts["COMPLETED"],
                "failed": counts["FAILED"],
                "cancelled": counts["CANCELLED"],
                "max_concurrent": self._max_concurrent,
                "workers_active": sum(1 for w in self._workers if not w.done()),
                "queue_size": self._pending_queue.qsize(),
            }

    async def get_task(self, task_id: str) -> Optional[Dict]:
        """
        الحصول على تفاصيل مهمة — Get task details as dict.

        Args / المعاملات:
            task_id: معرف المهمة — Task ID

        Returns / المخرجات:
            قاموس تفاصيل المهمة أو None — Task details dict or None
        """
        async with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            return None
        return {
            "id": task.id,
            "name": task.name,
            "priority": task.priority.name,
            "status": task.status,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "result": str(task.result)[:500] if task.result is not None else None,
            "error": task.error,
            "retries": task.retries,
            "max_retries": task.max_retries,
        }

    # ─────────────────────────────────────────────
    # الإيقاف / Shutdown
    # ─────────────────────────────────────────────

    async def stop(self) -> None:
        """
        إيقاف تدريجي — Graceful shutdown: cancel workers and wait.
        """
        logger.info("TaskQueue stopping — %d workers...", len(self._workers))
        self._running = False
        self._task_available.set()  # إيقاظ العمال للإلغاء — Wake workers for cancellation

        for w in self._workers:
            w.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        logger.info("TaskQueue stopped")
