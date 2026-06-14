"""
Adam Prism — Event Bus
========================
نظام أحداث غير متزامن للتواصل بين الموديولات بدون coupling.
كل موديول ينشر أحداث ويستمع لأحداث — بدون استيراد مباشر.

Features:
- Pub/Sub pattern with topic-based routing
- Async event processing with priority queues
- Event replay for late subscribers
- Dead letter queue for failed events
- Event persistence for audit trail
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum
from typing import Any

logger = logging.getLogger("adam_prism.orchestrator.event_bus")

class EventPriority(IntEnum):
    """أولوية الحدث — الأعلى يُنفذ أولاً"""
    CRITICAL = 0   # أحداث أمنية + إيقاف طوارئ
    HIGH = 1       # طلبات المستخدم + أخطاء حرجة
    NORMAL = 2     # عمليات عادية (chat, tool exec)
    LOW = 3        # تحليلات + تعلم + تسجيل
    BACKGROUND = 4 # تنظيف + إحصائيات + cache eviction

@dataclass
class Event:
    """حدث في النظام"""
    topic: str
    data: dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    source: str = ""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    replay: bool = False  # هل يُعاد بثه للمشتركين الجدد؟

    def __lt__(self, other):
        """لأجل priority queue — الأقل أولوية رقمياً = الأعلى أهمية"""
        if not isinstance(other, Event):
            return NotImplemented
        return self.priority < other.priority

class DeadLetterQueue:
    """طابور الأحداث الفاشلة — للمراجعة والإعادة"""

    def __init__(self, max_size: int = 1000):
        self._queue: list[dict[str, Any]] = []
        self._max_size = max_size

    def add(self, event: Event, error: str):
        """إضافة حدث فاشل"""
        entry = {
            "event_id": event.event_id,
            "topic": event.topic,
            "data": event.data,
            "source": event.source,
            "error": error,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._queue.append(entry)
        if len(self._queue) > self._max_size:
            self._queue = self._queue[-self._max_size:]
        logger.warning(f"DLQ: Event {event.event_id} on '{event.topic}' failed: {error}")

    def get_all(self) -> list[dict[str, Any]]:
        return list(self._queue)

    def clear(self):
        self._queue.clear()

    @property
    def size(self) -> int:
        return len(self._queue)

class EventBus:
    """
    ناقل أحداث غير متزامن — مركزي للتواصل بين الموديولات

    Usage:
        bus = EventBus()

        # Subscribe
        async def on_chat(event: Event):
            print(f"Chat: {event.data}")
        bus.subscribe("chat.message", on_chat)

        # Publish
        await bus.publish(Event(
            topic="chat.message",
            data={"user": "Mohamed", "message": "Hello"},
            source="api_server"
        ))
    """

    def __init__(self, replay_buffer_size: int = 100):
        # topic → list of handlers
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        # topic → wildcard pattern subscribers
        self._wildcard_subscribers: dict[str, list[Callable]] = defaultdict(list)
        # Replay buffer: topic → list of recent events
        self._replay_buffer: dict[str, list[Event]] = defaultdict(list)
        self._replay_buffer_size = replay_buffer_size
        # Dead letter queue
        self._dlq = DeadLetterQueue()
        # Stats
        self._published = 0
        self._delivered = 0
        self._failed = 0
        # Processing
        self._processing = False
        self._priority_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._worker_task: asyncio.Task | None = None
        self._tasks: set[asyncio.Task] = set()
        self._num_workers = 3

    def subscribe(self, topic: str, handler: Callable, replay: bool = False):
        """
        الاشتراك في موضوع
        - topic: اسم الموضوع (مثل "chat.message") أو نمط (مثل "chat.*")
        - handler: دالة async تأخذ Event
        - replay: هل نعيد بث الأحداث السابقة عند الاشتراك؟
        """
        if topic.endswith(".*"):
            self._wildcard_subscribers[topic[:-2]].append(handler)
            logger.info(f"EventBus: wildcard subscription '{topic}' → {handler.__name__}")
        else:
            self._subscribers[topic].append(handler)
            logger.info(f"EventBus: subscription '{topic}' → {handler.__name__}")

        if replay:
            # Replay recent events for this topic
            for event in self._replay_buffer.get(topic, []):
                try:
                    if asyncio.iscoroutinefunction(handler):
                        task = asyncio.create_task(handler(event))
                        self._tasks.add(task)
                        task.add_done_callback(self._tasks.discard)
                    else:
                        handler(event)
                except Exception as e:
                    logger.debug(f"Replay delivery failed for {topic}: {e}")

    def unsubscribe(self, topic: str, handler: Callable):
        """إلغاء الاشتراك"""
        if topic.endswith(".*"):
            base = topic[:-2]
            if base in self._wildcard_subscribers:
                self._wildcard_subscribers[base] = [
                    h for h in self._wildcard_subscribers[base] if h != handler
                ]
        else:
            if topic in self._subscribers:
                self._subscribers[topic] = [
                    h for h in self._subscribers[topic] if h != handler
                ]

    async def publish(self, event: Event):
        """
        نشر حدث — يُسلم لكل المشتركين غير متزامن
        """
        self._published += 1

        # Store in replay buffer if marked
        if event.replay:
            buf = self._replay_buffer[event.topic]
            buf.append(event)
            if len(buf) > self._replay_buffer_size:
                self._replay_buffer[event.topic] = buf[-self._replay_buffer_size:]

        # Deliver to direct subscribers
        handlers = list(self._subscribers.get(event.topic, []))
        # Deliver to wildcard subscribers
        for prefix, wild_handlers in self._wildcard_subscribers.items():
            if event.topic.startswith(prefix):
                handlers.extend(wild_handlers)

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                self._delivered += 1
            except Exception as e:
                self._failed += 1
                self._dlq.add(event, str(e))

    def publish_sync(self, event: Event):
        """نشر حدث بدون انتظار — يُنشئ task في الخلفية"""
        task = asyncio.create_task(self.publish(event))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def start_workers(self):
        """تشغيل عمال المعالجة من priority queue"""
        if self._processing:
            return
        self._processing = True
        for i in range(self._num_workers):
            task = asyncio.create_task(self._worker_loop(i))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
        logger.info(f"EventBus: {self._num_workers} workers started")

    async def _worker_loop(self, worker_id: int):
        """دورة عمل لمعالجة الأحداث من priority queue"""
        while self._processing:
            try:
                event = await asyncio.wait_for(
                    self._priority_queue.get(), timeout=1.0
                )
                await self.publish(event)
                self._priority_queue.task_done()
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("EventBus worker {worker_id} error:")

    async def enqueue(self, event: Event):
        """إضافة حدث لطابور الأولوية — يُعالج بواسطة workers"""
        await self._priority_queue.put(event)

    def stop_workers(self):
        """إيقاف العمال"""
        self._processing = False

    def get_subscribers(self, topic: str) -> list[str]:
        """أسماء المشتركين في موضوع"""
        handlers = self._subscribers.get(topic, [])
        return [h.__name__ for h in handlers if hasattr(h, '__name__')]

    @property
    def dlq(self) -> DeadLetterQueue:
        return self._dlq

    def stats(self) -> dict[str, Any]:
        return {
            "published": self._published,
            "delivered": self._delivered,
            "failed": self._failed,
            "topics": list(self._subscribers.keys()),
            "wildcard_topics": list(self._wildcard_subscribers.keys()),
            "dlq_size": self._dlq.size,
            "replay_buffer_topics": list(self._replay_buffer.keys()),
            "workers_running": self._processing,
        }
