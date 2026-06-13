"""
Adam Prism — Lightweight Tracing
====================================
تتبع خفيف بدون اعتماديات خارجية.

A zero-dependency lightweight tracing system that tracks spans,
measures timing, detects slow operations, and can export to JSON.
Optionally integrates with OpenTelemetry if available.

المميزات / Features:
  - تتبع Span بدون اعتماديات — Zero-dependency span tracking
  - كشف العمليات البطيئة — Slow span detection
  - تصدير JSON — JSON export
  - يعمل كـ context manager — Works as context manager
  - تكامل اختياري مع OpenTelemetry — Optional OpenTelemetry export
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("adam_prism.observability.tracing")


# ═══════════════════════════════════════════════════════════════
# أنماط البيانات / Data Models
# ═══════════════════════════════════════════════════════════════

class SpanStatus(str):
    """
    حالة Span — Span status.
    """
    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


@dataclass
class SpanEvent:
    """
    حدث داخل Span — An event within a span.

    Attributes / الخصائص:
        name: اسم الحدث — Event name
        timestamp: وقت الحدث — Event timestamp
        attributes: سمات الحدث — Event attributes
    """
    name: str
    timestamp: float = field(default_factory=time.time)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """
    وحدة تتبع — A tracing span.

    يمثل عملية واحدة في التتبع، مع بداية ونهاية وسمات وأحداث.
    Represents a single operation in a trace, with start/end times,
    attributes, and events.

    Attributes / الخصائص:
        id: معرف Span الفريد — Unique span ID
        name: اسم العملية — Operation name
        start_time: وقت البدء — Start timestamp (epoch)
        end_time: وقت الانتهاء — End timestamp (epoch)
        attributes: سمات مخصصة — Custom attributes
        status: حالة Span — Span status
        events: قائمة الأحداث — List of events
        parent_id: معرف Span الأب — Parent span ID
        trace_id: معرف التتبع — Trace ID
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:16])
    name: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = SpanStatus.UNSET
    events: list[SpanEvent] = field(default_factory=list)
    parent_id: str | None = None
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:32])

    @property
    def duration_ms(self) -> float:
        """
        المدة بالمللي ثانية — Duration in milliseconds.
        """
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time) * 1000
        if self.start_time:
            return (time.time() - self.start_time) * 1000
        return 0.0

    def set_attribute(self, key: str, value: Any) -> None:
        """
        تعيين سمة — Set an attribute on the span.
        """
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """
        إضافة حدث — Add an event to the span.
        """
        self.events.append(SpanEvent(name=name, attributes=attributes or {}))

    def set_status(self, status: str, description: str = "") -> None:
        """
        تعيين الحالة — Set the span status.
        """
        self.status = status
        if description:
            self.attributes["status_description"] = description

    def to_dict(self) -> dict[str, Any]:
        """
        تحويل إلى قاموس — Convert to dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "attributes": self.attributes,
            "events": [
                {
                    "name": e.name,
                    "timestamp": e.timestamp,
                    "attributes": e.attributes,
                }
                for e in self.events
            ],
        }


# ═══════════════════════════════════════════════════════════════
# Adam Tracer
# ═══════════════════════════════════════════════════════════════

class AdamTracer:
    """
    متتبع خفيف — Lightweight tracer for Adam Prism.

    يوفر تتبع Span بدون اعتماديات خارجية مع كشف العمليات البطيئة
    وتصدير JSON. يمكنه التكامل اختيارياً مع OpenTelemetry.

    Provides span tracking without external dependencies, with slow span
    detection and JSON export. Can optionally integrate with OpenTelemetry.

    الاستخدام / Usage:
        tracer = AdamTracer(slow_threshold_ms=5000)

        # كـ context manager — As context manager
        async with tracer.span("chat_request") as s:
            s.set_attribute("user", "user_1")
            # ... العملية — ... the operation
            s.set_status(SpanStatus.OK)

        # يدوياً — Manually
        span = tracer.start_span("database_query")
        try:
            # ... العملية — ... the operation
            span.set_status(SpanStatus.OK)
        except Exception as e:
            span.set_status(SpanStatus.ERROR, str(e))
            raise
        finally:
            tracer.end_span(span)
    """

    def __init__(
        self,
        slow_threshold_ms: float = 5000.0,
        max_spans: int = 1000,
    ) -> None:
        """
        تهيئة المتتبع — Initialize the tracer.

        Args / المعاملات:
            slow_threshold_ms: عتبة البطء بالمللي ثانية — Slow span threshold in ms
            max_spans: الحد الأقصى لعدد Span المحفوظة — Max stored spans
        """
        self._slow_threshold_ms = slow_threshold_ms
        self._max_spans = max_spans
        self._spans: dict[str, Span] = {}
        self._active_spans: dict[str, Span] = {}

        # عدادات — Counters
        self._total_spans: int = 0
        self._slow_spans: int = 0
        self._error_spans: int = 0

    # ─────────────────────────────────────────────
    # إنهاء Span / Span Lifecycle
    # ─────────────────────────────────────────────

    def start_span(
        self,
        name: str,
        parent: Span | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """
        بدء Span — Start a new span.

        Args / المعاملات:
            name: اسم العملية — Operation name
            parent: Span الأب — Parent span
            attributes: سمات أولية — Initial attributes

        Returns / المخرجات:
            Span الجديد — The new span
        """
        span = Span(
            name=name,
            start_time=time.time(),
            parent_id=parent.id if parent else None,
            trace_id=parent.trace_id if parent else str(uuid.uuid4())[:32],
            attributes=attributes or {},
        )

        self._spans[span.id] = span
        self._active_spans[span.id] = span
        self._total_spans += 1

        # تنظيف Spans القديمة — Clean up old spans if over limit
        if len(self._spans) > self._max_spans:
            oldest_ids = sorted(
                self._spans.keys(),
                key=lambda s: self._spans[s].start_time,
            )[: len(self._spans) - self._max_spans]
            for sid in oldest_ids:
                self._spans.pop(sid, None)

        return span

    def end_span(self, span: Span) -> None:
        """
        إنهاء Span — End a span.

        Args / المعاملات:
            span: Span المراد إنهاؤه — The span to end
        """
        span.end_time = time.time()
        self._active_spans.pop(span.id, None)

        # كشف البطء — Detect slow span
        if span.duration_ms > self._slow_threshold_ms:
            self._slow_spans += 1
            logger.warning(
                "Slow span detected: '%s' took %.1fms (threshold: %.1fms)",
                span.name, span.duration_ms, self._slow_threshold_ms,
            )

        # كشف الخطأ — Detect error
        if span.status == SpanStatus.ERROR:
            self._error_spans += 1

        logger.debug(
            "Span '%s' ended: %.1fms [%s]",
            span.name, span.duration_ms, span.status,
        )

    # ─────────────────────────────────────────────
    # Context Manager
    # ─────────────────────────────────────────────

    @asynccontextmanager
    async def span(
        self,
        name: str,
        parent: Span | None = None,
        attributes: dict[str, Any] | None = None,
    ):
        """
        Context manager لإنشاء Span — Async context manager for spans.

        Args / المعاملات:
            name: اسم العملية — Operation name
            parent: Span الأب — Parent span
            attributes: سمات أولية — Initial attributes

        Yields / ينتج:
            Span الجديد — The new span

        Usage / الاستخدام:
            async with tracer.span("operation") as s:
                s.set_attribute("key", "value")
                # ... العملية — ... the operation
        """
        s = self.start_span(name, parent=parent, attributes=attributes)
        try:
            yield s
            if s.status == SpanStatus.UNSET:
                s.set_status(SpanStatus.OK)
        except Exception as exc:
            s.set_status(SpanStatus.ERROR, str(exc))
            s.add_event("exception", {"type": type(exc).__name__, "message": str(exc)[:500]})
            raise
        finally:
            self.end_span(s)

    # ─────────────────────────────────────────────
    # استخراج البيانات / Data Extraction
    # ─────────────────────────────────────────────

    def get_trace(self, span: Span) -> dict[str, Any]:
        """
        الحصول على التتبع الكامل — Get the full trace for a span.

        يجمع كل Spans ذات نفس trace_id.
        Collects all spans with the same trace_id.

        Args / المعاملات:
            span: Span مرجعي — Reference span

        Returns / المخرجات:
            التتبع الكامل كقاموس — Full trace as dict
        """
        trace_spans = [
            s.to_dict() for s in self._spans.values()
            if s.trace_id == span.trace_id
        ]
        # ترتيب حسب وقت البدء — Sort by start time
        trace_spans.sort(key=lambda s: s["start_time"])

        return {
            "trace_id": span.trace_id,
            "spans": trace_spans,
            "span_count": len(trace_spans),
        }

    def export_json(self, span: Span) -> str:
        """
        تصدير Span كـ JSON — Export a span (and its trace) as JSON.

        Args / المعاملات:
            span: Span المراد تصديره — Span to export

        Returns / المخرجات:
            JSON string للتتبع — JSON string of the trace
        """
        import json
        trace = self.get_trace(span)
        return json.dumps(trace, indent=2, ensure_ascii=False, default=str)

    # ─────────────────────────────────────────────
    # تكامل OpenTelemetry / OpenTelemetry Integration
    # ─────────────────────────────────────────────

    def export_to_otel(self, span: Span) -> Any | None:
        """
        تصدير Span إلى OpenTelemetry — Export span to OpenTelemetry (if available).

        هذه الدالة تحاول استخدام OpenTelemetry إذا كان مثبتاً.
        This function attempts to use OpenTelemetry if it's installed.

        Args / المعاملات:
            span: Span المراد تصديره — Span to export

        Returns / المخرجات:
            كائن OpenTelemetry Span أو None — OTel span object or None
        """
        try:
            from opentelemetry import trace as otel_trace

            tracer = otel_trace.get_tracer("adam_prism")
            otel_span = tracer.start_span(span.name)

            # تعيين السمات — Set attributes
            for key, value in span.attributes.items():
                with suppress(Exception):
                    otel_span.set_attribute(key, str(value)[:256])

            # تعيين الحالة — Set status
            if span.status == SpanStatus.OK:
                otel_span.set_status(otel_trace.StatusCode.OK)
            elif span.status == SpanStatus.ERROR:
                otel_span.set_status(otel_trace.StatusCode.ERROR)

            if span.end_time:
                otel_span.end()

            return otel_span

        except ImportError:
            logger.debug("OpenTelemetry not available — skipping OTel export")
            return None
        except Exception as exc:
            logger.warning("OTel export failed: %s", exc)
            return None

    # ─────────────────────────────────────────────
    # إحصائيات / Statistics
    # ─────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """
        الحصول على إحصائيات المتتبع — Get tracer statistics.

        Returns / المخرجات:
            إحصائيات — Stats dict
        """
        return {
            "total_spans": self._total_spans,
            "active_spans": len(self._active_spans),
            "stored_spans": len(self._spans),
            "slow_spans": self._slow_spans,
            "error_spans": self._error_spans,
            "slow_threshold_ms": self._slow_threshold_ms,
            "max_spans": self._max_spans,
        }


# ═══════════════════════════════════════════════════════════════
# Global Tracer Instance
# ═══════════════════════════════════════════════════════════════

# مثيل عالمي — Global tracer instance for convenience
_global_tracer: AdamTracer | None = None


def get_tracer() -> AdamTracer:
    """
    الحصول على المتتبع العالمي — Get the global tracer instance.

    Returns / المخرجات:
        المتتبع العالمي — Global AdamTracer
    """
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = AdamTracer()
    return _global_tracer


def set_tracer(tracer: AdamTracer) -> None:
    """
    تعيين المتتبع العالمي — Set the global tracer instance.

    Args / المعاملات:
        tracer: المتتبع — The tracer to set
    """
    global _global_tracer
    _global_tracer = tracer
