"""
Adam Prism — Async Event Bus
==============================
ناقل أحداث غير متزامن مع دعم الأولويات والـ wildcard والتخزين المؤقت.

An event-driven communication backbone for inter-module messaging.
Supports wildcard topic subscriptions, priority-based delivery, dead-letter
queue for failed events, and replay buffer for late subscribers.

المميزات / Features:
  - أولويات الأحداث (CRITICAL → LOW) — Event priorities
  - دعم الـ wildcard في المواضيع (chat.*) — Wildcard topic matching
  - تخزين مؤقت لإعادة تشغيل الأحداث — Replay buffer for new subscribers
  - طابور الرسائل الميتة للرسائل الفاشلة — Dead-letter queue for failures
  - تجمع عمال قابل للتكوين — Configurable worker pool
  - إحصائيات شاملة — Comprehensive stats
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

logger = logging.getLogger("adam_prism.orchestrator.event_bus")


# ═══════════════════════════════════════════════════════════════
# أنماط البيانات / Data Models
# ═══════════════════════════════════════════════════════════════

class EventPriority(IntEnum):
    """
    أولوية الحدث — كلما زادت القيمة، زادت الأولوية.
    Event priority — higher value = higher priority.
    """
    LOW = 0
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class Event:
    """
    حدث في ناقل الأحداث — An event on the bus.

    Attributes / الخصائص:
        id: معرف فريد للحدث — Unique event identifier
        topic: موضوع الحدث (يدعم التسلسل الهرمي مثل chat.message) — Event topic
        data: بيانات الحدث — Event payload
        priority: أولوية الحدث — Event priority
        timestamp: وقت الإنشاء — Creation timestamp (epoch)
        source: مصدر الحدث — Event source module name
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    data: Any = None
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    source: str = ""


@dataclass
class DeadLetterEntry:
    """
    رسالة ميتة — حدث فشل تسليمه.
    A dead-letter entry for an event that could not be delivered.
    """
    event: Event
    subscriber_id: str
    error: str
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0


@dataclass
class _Subscription:
    """
    اشتراك داخلي — Internal subscription record.

    Attributes / الخصائص:
        id: معرف الاشتراك — Subscription identifier
        topic_pattern: نمط الموضوع (قد يحتوي على wildcard) — Topic pattern
        callback: دالة الاستدعاء — Async callback function
        priority_filter: تصفية حسب الأولوية (اختياري) — Optional priority filter
        is_wildcard: هل النمط يحتوي على wildcard — Whether pattern uses wildcards
    """
    id: str
    topic_pattern: str
    callback: Callable[[Event], Coroutine[Any, Any, None]]
    priority_filter: Optional[EventPriority] = None
    is_wildcard: bool = False


# ═══════════════════════════════════════════════════════════════
# ناقل الأحداث / Event Bus
# ═══════════════════════════════════════════════════════════════

class EventBus:
    """
    ناقل أحداث غير متزامن — Async event bus with priority, wildcard, and replay.

    الاستخدام الأساسي / Basic Usage:
        bus = EventBus()
        await bus.subscribe("chat.message", on_chat_message)
        await bus.publish_data("chat.message", {"text": "مرحبا"})

    يدعم / Supports:
      - wildcard مثل "chat.*" يطابق "chat.message" و "chat.tool_call"
      - تصفية حسب الأولوية — Priority filtering
      - إعادة تشغيل الأحداث الأخيرة للمشتركين الجدد — Replay buffer
      - طابور الرسائل الميتة — Dead-letter queue
      - تجمع عمال — Worker pool for concurrent delivery
    """

    def __init__(
        self,
        replay_buffer_size: int = 100,
        max_dlq_size: int = 1000,
        worker_count: int = 4,
    ) -> None:
        """
        تهيئة ناقل الأحداث — Initialize the event bus.

        Args / المعاملات:
            replay_buffer_size: حجم المخزن المؤقت لإعادة التشغيل — Replay buffer size
            max_dlq_size: الحد الأقصى لطابور الرسائل الميتة — Max dead-letter queue size
            worker_count: عدد عمال التسليم — Number of delivery workers
        """
        self._subscriptions: Dict[str, _Subscription] = {}
        self._replay_buffer: List[Event] = []
        self._replay_buffer_size = replay_buffer_size
        self._dead_letter_queue: List[DeadLetterEntry] = []
        self._max_dlq_size = max_dlq_size

        # طابور الأحداث الداخلية — Internal event queue (priority-sorted)
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

        # تجمع العمال — Worker pool
        self._worker_count = worker_count
        self._workers: List[asyncio.Task] = []
        self._running = False

        # عدادات الإحصائيات — Stats counters
        self._total_published: int = 0
        self._total_delivered: int = 0
        self._total_failed: int = 0

        # قفل لسلامة العمليات — Lock for thread safety on shared state
        self._lock = asyncio.Lock()

    # ─────────────────────────────────────────────
    # الاشتراك / Subscription
    # ─────────────────────────────────────────────

    async def subscribe(
        self,
        topic: str,
        callback: Callable[[Event], Coroutine[Any, Any, None]],
        priority_filter: Optional[EventPriority] = None,
    ) -> str:
        """
        الاشتراك في موضوع — Subscribe to a topic.

        Args / المعاملات:
            topic: الموضوع أو نمط wildcard (مثلاً "chat.*") — Topic or wildcard pattern
            callback: دالة async تُستدعى عند وصول حدث — Async callback
            priority_filter: إذا تم تحديده، استقبل فقط الأحداث بهذه الأولوية أو أعلى
                             — If set, only receive events at this priority or above

        Returns / المخرجات:
            معرف الاشتراك — Subscription ID (for unsubscribe)

        Note / ملاحظة:
            إذا كان الموضوع يحتوي على "*" يُعامَل كـ wildcard.
            "chat.*" يطابق "chat.message" و "chat.tool_call" لكن لا يطابق "chat".
        """
        sub_id = str(uuid.uuid4())
        is_wildcard = "*" in topic

        sub = _Subscription(
            id=sub_id,
            topic_pattern=topic,
            callback=callback,
            priority_filter=priority_filter,
            is_wildcard=is_wildcard,
        )

        async with self._lock:
            self._subscriptions[sub_id] = sub

        # إعادة تشغيل الأحداث السابقة — Replay recent events for late subscriber
        replayed = 0
        for event in self._replay_buffer:
            if self._topic_matches(sub.topic_pattern, event.topic, sub.is_wildcard):
                if priority_filter is not None and event.priority < priority_filter:
                    continue
                try:
                    await callback(event)
                    replayed += 1
                except Exception as exc:
                    logger.warning(
                        "Replay delivery failed for subscriber %s on topic %s: %s",
                        sub_id, event.topic, exc,
                    )

        logger.info(
            "Subscribed [%s] to topic '%s'%s (replayed %d events)",
            sub_id[:8], topic,
            f" [wildcard]" if is_wildcard else "",
            replayed,
        )
        return sub_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        إلغاء الاشتراك — Unsubscribe by subscription ID.

        Args / المعاملات:
            subscription_id: معرف الاشتراك — The ID returned from subscribe()

        Returns / المخرجات:
            True إذا تم إلغاء الاشتراك، False إذا لم يُوجَد — True if removed
        """
        async with self._lock:
            removed = self._subscriptions.pop(subscription_id, None)
        if removed:
            logger.info("Unsubscribed [%s] from '%s'", subscription_id[:8], removed.topic_pattern)
            return True
        logger.warning("Unsubscribe failed — ID %s not found", subscription_id[:8])
        return False

    # ─────────────────────────────────────────────
    # النشر / Publishing
    # ─────────────────────────────────────────────

    async def publish(self, event: Event) -> int:
        """
        نشر حدث — Publish an event to all matching subscribers.

        Args / المعاملات:
            event: الحدث المراد نشره — The event to publish

        Returns / المخرجات:
            عدد المشتركين الذين سيستلمون الحدث — Number of subscribers that will receive it
        """
        self._total_published += 1

        # حفظ في المخزن المؤقت — Store in replay buffer
        async with self._lock:
            self._replay_buffer.append(event)
            if len(self._replay_buffer) > self._replay_buffer_size:
                self._replay_buffer = self._replay_buffer[-self._replay_buffer_size:]

        # إضافة إلى الطابور — Enqueue for worker delivery
        # PriorityQueue يرتب حسب الأولوية (سالب لأننا نريد أعلى أولوية أولاً)
        await self._queue.put((-event.priority, event.timestamp, event))

        # حساب عدد المستلمين — Count matching subscribers
        async with self._lock:
            count = sum(
                1 for s in self._subscriptions.values()
                if self._topic_matches(s.topic_pattern, event.topic, s.is_wildcard)
                and (s.priority_filter is None or event.priority >= s.priority_filter)
            )

        logger.debug(
            "Published event %s on topic '%s' to %d subscribers [priority=%s]",
            event.id[:8], event.topic, count, event.priority.name,
        )
        return count

    async def publish_data(
        self,
        topic: str,
        data: Any,
        priority: EventPriority = EventPriority.NORMAL,
        source: str = "",
    ) -> int:
        """
        نشر بيانات كحدث — Publish data as an event (convenience method).

        Args / المعاملات:
            topic: موضوع الحدث — Event topic
            data: بيانات الحدث — Event payload
            priority: أولوية الحدث — Event priority
            source: مصدر الحدث — Event source

        Returns / المخرجات:
            عدد المشتركين الذين سيستلمون الحدث — Number of matching subscribers
        """
        event = Event(
            topic=topic,
            data=data,
            priority=priority,
            source=source,
        )
        return await self.publish(event)

    # ─────────────────────────────────────────────
    # تجمع العمال / Worker Pool
    # ─────────────────────────────────────────────

    async def start(self) -> None:
        """
        بدء تجمع العمال — Start the event delivery worker pool.
        يجب استدعاؤها قبل أن يبدأ نشر الأحداث في الخلفية.
        Must be called to start background event delivery.
        """
        if self._running:
            logger.warning("EventBus already running — ignoring start()")
            return

        self._running = True
        for i in range(self._worker_count):
            task = asyncio.create_task(self._worker_loop(i), name=f"eventbus-worker-{i}")
            self._workers.append(task)

        logger.info("EventBus started with %d workers", self._worker_count)

    async def _worker_loop(self, worker_id: int) -> None:
        """
        حلقة العامل — Worker loop that processes events from the priority queue.
        """
        while self._running:
            try:
                # انتظار حدث مع مهلة — Wait for event with timeout
                try:
                    neg_priority, ts, event = await asyncio.wait_for(
                        self._queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                await self._deliver_event(event)

            except asyncio.CancelledError:
                logger.debug("Worker %d cancelled", worker_id)
                break
            except Exception as exc:
                logger.error("Worker %d unexpected error: %s", worker_id, exc, exc_info=True)

    async def _deliver_event(self, event: Event) -> None:
        """
        تسليم حدث لجميع المشتركين المتطابقين — Deliver an event to all matching subscribers.
        """
        async with self._lock:
            matching = [
                s for s in self._subscriptions.values()
                if self._topic_matches(s.topic_pattern, event.topic, s.is_wildcard)
                and (s.priority_filter is None or event.priority >= s.priority_filter)
            ]

        if not matching:
            return

        # تسليم متوازي — Parallel delivery
        results = await asyncio.gather(
            *[self._safe_call(sub, event) for sub in matching],
            return_exceptions=True,
        )

        for sub, result in zip(matching, results):
            if isinstance(result, Exception):
                self._total_failed += 1
                await self._enqueue_dead_letter(event, sub.id, str(result))
            else:
                self._total_delivered += 1

    async def _safe_call(self, sub: _Subscription, event: Event) -> None:
        """
        استدعاء آمن مع مهلة — Safe callback invocation with timeout.
        """
        try:
            await asyncio.wait_for(sub.callback(event), timeout=30.0)
        except asyncio.TimeoutError:
            raise RuntimeError(f"Callback timeout (30s) for subscriber {sub.id[:8]} on {event.topic}")
        except Exception as exc:
            raise RuntimeError(f"Callback error for subscriber {sub.id[:8]}: {exc}") from exc

    # ─────────────────────────────────────────────
    # طابور الرسائل الميتة / Dead-Letter Queue
    # ─────────────────────────────────────────────

    async def _enqueue_dead_letter(self, event: Event, subscriber_id: str, error: str) -> None:
        """
        إضافة حدث فاشل إلى طابور الرسائل الميتة — Add failed event to DLQ.
        """
        entry = DeadLetterEntry(
            event=event,
            subscriber_id=subscriber_id,
            error=error,
        )

        async with self._lock:
            self._dead_letter_queue.append(entry)
            if len(self._dead_letter_queue) > self._max_dlq_size:
                self._dead_letter_queue = self._dead_letter_queue[-self._max_dlq_size:]

        logger.warning(
            "Dead-letter: event %s for subscriber %s — %s",
            event.id[:8], subscriber_id[:8], error[:120],
        )

    async def get_dead_letters(self, limit: int = 50) -> List[Dict]:
        """
        الحصول على رسائل ميتة — Retrieve dead-letter entries.

        Args / المعاملات:
            limit: الحد الأقصى للعدد — Max entries to return

        Returns / المخرجات:
            قائمة بالرسائل الميتة كقواميس — List of dead-letter entries as dicts
        """
        async with self._lock:
            entries = self._dead_letter_queue[-limit:]
        return [
            {
                "event_id": e.event.id,
                "topic": e.event.topic,
                "subscriber_id": e.subscriber_id,
                "error": e.error,
                "timestamp": e.timestamp,
                "retry_count": e.retry_count,
            }
            for e in entries
        ]

    # ─────────────────────────────────────────────
    # مطابقة المواضيع / Topic Matching
    # ─────────────────────────────────────────────

    @staticmethod
    def _topic_matches(pattern: str, topic: str, is_wildcard: bool) -> bool:
        """
        مطابقة موضوع مع نمط — Check if a topic matches a pattern.

        القواعد / Rules:
          - تطابق تام: "chat.message" == "chat.message"
          - wildcard نهائي: "chat.*" يطابق "chat.message" و "chat.tool_call"
          - wildcard لا يطابق مستويات أعمق: "chat.*" لا يطابق "chat.sub.deep"
        """
        if not is_wildcard:
            return pattern == topic

        # نمط wildcard — Wildcard pattern
        if not pattern.endswith(".*"):
            # إذا كان النمط لا ينتهي بـ .* فاعتبره wildcard بسيط
            prefix = pattern.rstrip("*").rstrip(".")
            return topic == prefix or topic.startswith(prefix + ".")

        # نمط مثل "chat.*" — Pattern like "chat.*"
        prefix = pattern[:-2]  # إزالة ".*" — Remove ".*"
        if not topic.startswith(prefix + "."):
            return False
        remainder = topic[len(prefix) + 1:]
        # يجب أن يكون مستوى واحد فقط — Must be single level
        return "." not in remainder

    # ─────────────────────────────────────────────
    # الإحصائيات والتشغيل / Stats & Operations
    # ─────────────────────────────────────────────

    async def get_stats(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات ناقل الأحداث — Get event bus statistics.

        Returns / المخرجات:
            قاموس يحتوي على:
            - subscriber_count: عدد المشتركين
            - total_published: إجمالي الأحداث المنشورة
            - total_delivered: إجمالي الأحداث المسلمة
            - total_failed: إجمالي الأحداث الفاشلة
            - dlq_count: عدد الرسائل الميتة
            - replay_buffer_size: حجم المخزن المؤقت
            - queue_size: حجم الطابور الحالي
            - topics: قائمة المواضيع الفريدة
        """
        async with self._lock:
            topics: Set[str] = set()
            for s in self._subscriptions.values():
                topics.add(s.topic_pattern)

            return {
                "subscriber_count": len(self._subscriptions),
                "total_published": self._total_published,
                "total_delivered": self._total_delivered,
                "total_failed": self._total_failed,
                "dlq_count": len(self._dead_letter_queue),
                "replay_buffer_size": len(self._replay_buffer),
                "queue_size": self._queue.qsize(),
                "topics": sorted(topics),
                "workers_active": sum(1 for w in self._workers if not w.done()),
            }

    async def flush(self) -> None:
        """
        إيقاف تدريجي — Graceful shutdown: stop workers and drain queue.
        """
        logger.info("EventBus flushing — stopping %d workers...", len(self._workers))
        self._running = False

        # إلغاء العمال — Cancel workers
        for w in self._workers:
            w.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        # تسليم الأحداث المتبقية — Drain remaining events
        remaining = 0
        while not self._queue.empty():
            try:
                _, _, event = self._queue.get_nowait()
                await self._deliver_event(event)
                remaining += 1
            except asyncio.QueueEmpty:
                break

        logger.info("EventBus flushed — delivered %d remaining events", remaining)
