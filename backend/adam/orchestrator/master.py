"""
Adam Prism — Master Orchestrator
===================================
العقل المركزي الذي ينسق كل موديولات النظام.

The central orchestration brain that ties all modules together through
smart request routing, workflow execution, health monitoring, adaptive
learning, and graceful degradation.

المميزات / Features:
  - توجيه ذكي للطلبات — Smart request routing based on type and learned patterns
  - مراقبة صحة الموديولات — Module health monitoring with circuit breaker
  - تنفيذ سير عمل متعدد الخطوات — Multi-step workflow execution
  - تعلم تكيفي — Adaptive learning from event patterns
  - تدهور تدريجي عند الفشل — Graceful degradation when modules fail
  - قاطع الدائرة — Circuit breaker integration
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from adam.orchestrator.event_bus import EventBus, Event, EventPriority
from adam.orchestrator.task_queue import TaskQueue, Task, TaskPriority

logger = logging.getLogger("adam_prism.orchestrator.master")


# ═══════════════════════════════════════════════════════════════
# أنماط البيانات / Data Models
# ═══════════════════════════════════════════════════════════════

class RequestType(str, Enum):
    """
    أنواع الطلبات — Request type classification for routing.
    """
    CHAT = "CHAT"
    CODE_GENERATION = "CODE_GENERATION"
    RESEARCH = "RESEARCH"
    ANALYSIS = "ANALYSIS"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    WORKFLOW = "WORKFLOW"
    SYSTEM = "SYSTEM"


@dataclass
class ModuleHealth:
    """
    حالة صحة موديول — Module health status.

    Attributes / الخصائص:
        name: اسم الموديول — Module name
        healthy: هل الموديول يعمل؟ — Is the module healthy?
        last_check: وقت آخر فحص — Last health check timestamp
        failure_count: عدد الإخفاقات المتتالية — Consecutive failure count
        latency_ms: زمن الاستجابة بالمللي ثانية — Response latency in ms
    """
    name: str
    healthy: bool = True
    last_check: float = field(default_factory=time.time)
    failure_count: int = 0
    latency_ms: float = 0.0


@dataclass
class WorkflowStep:
    """
    خطوة في سير العمل — A step in a workflow.

    Attributes / الخصائص:
        name: اسم الخطوة — Step name
        module: الموديول المسؤول — Responsible module
        action: الإجراء المطلوب — Action to perform
        status: حالة الخطوة — Step status
        result: النتيجة — Step result
        error: رسالة الخطأ — Error message if failed
    """
    name: str
    module: str
    action: str
    status: str = "PENDING"
    result: Any = None
    error: Optional[str] = None


@dataclass
class Workflow:
    """
    سير عمل متعدد الخطوات — A multi-step workflow.

    Attributes / الخصائص:
        id: معرف فريد — Unique identifier
        name: اسم سير العمل — Workflow name
        steps: قائمة الخطوات — List of steps
        current_step: الفهرس الحالي — Current step index
        status: الحالة — Workflow status
        created_at: وقت الإنشاء — Creation timestamp
        result: النتيجة النهائية — Final result
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    current_step: int = 0
    status: str = "PENDING"
    created_at: float = field(default_factory=time.time)
    result: Any = None


# ═══════════════════════════════════════════════════════════════
# خريطة التوجيه / Routing Map
# ═══════════════════════════════════════════════════════════════

# التوجيه الافتراضي: نوع الطلب → الموديول المفضل
# Default routing: request type → preferred module(s)
_DEFAULT_ROUTE_MAP: Dict[RequestType, List[str]] = {
    RequestType.CHAT: ["engine", "provider"],
    RequestType.CODE_GENERATION: ["engine", "provider"],
    RequestType.RESEARCH: ["engine", "memory", "eyes"],
    RequestType.ANALYSIS: ["engine", "memory", "knowledge"],
    RequestType.TOOL_EXECUTION: ["engine", "tools"],
    RequestType.WORKFLOW: ["orchestrator", "engine"],
    RequestType.SYSTEM: ["orchestrator"],
}

# التدهور البديل: الموديول الفاشل → البديل
# Fallback map: failed module → fallback module(s)
_FALLBACK_MAP: Dict[str, List[str]] = {
    "memory": ["knowledge", "notebook"],
    "knowledge": ["memory", "eyes"],
    "eyes": ["tools", "knowledge"],
    "tools": ["engine"],
    "ethics": ["security_guard"],
    "security_guard": ["ethics"],
    "notebook": ["memory"],
    "provider": [],  # لا بديل — no fallback for provider
    "engine": [],    # لا بديل — no fallback for engine
}


# ═══════════════════════════════════════════════════════════════
# Master Orchestrator
# ═══════════════════════════════════════════════════════════════

class MasterOrchestrator:
    """
    المنسق الرئيسي — العقل المركزي لنظام آدم بريزم.

    The Master Orchestrator is the central brain that:
      1. Routes requests to the appropriate module(s) — يوجه الطلبات
      2. Monitors module health — يراقب صحة الموديولات
      3. Executes multi-step workflows — ينفذ سير العمل
      4. Learns from patterns — يتعلم من الأنماط
      5. Handles graceful degradation — يتعامل مع التدهور

    الاستخدام / Usage:
        master = MasterOrchestrator(engine)
        await master.start()
        result = await master.route_request(RequestType.CHAT, {"message": "مرحبا"})
        await master.stop()
    """

    def __init__(
        self,
        engine: Any,
        event_bus: Optional[EventBus] = None,
        task_queue: Optional[TaskQueue] = None,
        health_check_interval: float = 30.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_recovery: float = 60.0,
    ) -> None:
        """
        تهيئة المنسق — Initialize the Master Orchestrator.

        Args / المعاملات:
            engine: مرجع المحرك الرئيسي — Reference to the main engine
            event_bus: ناقل الأحداث (يُنشأ تلقائياً إذا لم يُحدد) — Event bus
            task_queue: طابور المهام (يُنشأ تلقائياً إذا لم يُحدد) — Task queue
            health_check_interval: فترة فحص الصحة بالثواني — Health check interval
            circuit_breaker_threshold: عدد الإخفاقات قبل الفتح — CB threshold
            circuit_breaker_recovery: مدة التعافي بالثواني — CB recovery time
        """
        self.engine = engine
        self.event_bus = event_bus or EventBus()
        self.task_queue = task_queue or TaskQueue()

        self._health_check_interval = health_check_interval
        self._cb_threshold = circuit_breaker_threshold
        self._cb_recovery = circuit_breaker_recovery

        # صحة الموديولات — Module health records
        self._module_health: Dict[str, ModuleHealth] = {}

        # قاطع الدائرة — Circuit breaker state
        self._circuit_open: Dict[str, bool] = {}
        self._circuit_opened_at: Dict[str, float] = {}

        # أوزان التوجيه التكيفية — Adaptive routing weights
        self._routing_weights: Dict[str, Dict[str, float]] = {}
        for rt in RequestType:
            self._routing_weights[rt.value] = {}

        # سجلات سير العمل — Workflow records
        self._workflows: Dict[str, Workflow] = {}

        # مهام الخلفية — Background tasks
        self._health_task: Optional[asyncio.Task] = None
        self._running = False

        # اشتراك في الأحداث — Subscribe to events for learning
        self._event_sub_id: Optional[str] = None

    # ─────────────────────────────────────────────
    # التوجيه الذكي / Smart Routing
    # ─────────────────────────────────────────────

    async def route_request(
        self,
        request_type: RequestType,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        توجيه طلب ذكي — Smart route a request to the appropriate module(s).

        الخوارزمية / Algorithm:
          1. تحديد الموديولات المفضلة من خريطة التوجيه
          2. تطبيق أوزان التعلم التكيفي
          3. تجاوز الموديولات المعطلة (قاطع الدائرة مفتوح)
          4. محاولة كل موديول بالترتيب حتى النجاح
          5. التدهور البديل إذا فشل الكل

        Args / المعاملات:
            request_type: نوع الطلب — Request type
            data: بيانات الطلب — Request data

        Returns / المخرجات:
            نتيجة التوجيه — Routing result dict with module, success, result/error
        """
        # الموديولات المرشحة — Candidate modules
        candidates = list(_DEFAULT_ROUTE_MAP.get(request_type, ["engine"]))

        # ترتيب حسب الأوزان التكيفية — Sort by adaptive weights
        weights = self._routing_weights.get(request_type.value, {})
        if weights:
            candidates.sort(key=lambda m: weights.get(m, 0.0), reverse=True)

        # محاولة كل موديول — Try each module
        for module_name in candidates:
            if self._is_circuit_open(module_name):
                logger.warning(
                    "Circuit breaker open for '%s' — skipping", module_name,
                )
                continue

            try:
                result = await self._dispatch_to_module(module_name, request_type, data)
                # نجاح — تحديث الأوزان — Success: update weights
                self._update_weight(request_type.value, module_name, success=True)
                await self.event_bus.publish_data(
                    "orchestrator.route_success",
                    {"module": module_name, "request_type": request_type.value},
                    priority=EventPriority.LOW,
                    source="master",
                )
                return {
                    "module": module_name,
                    "success": True,
                    "result": result,
                }
            except Exception as exc:
                logger.warning(
                    "Module '%s' failed for %s: %s",
                    module_name, request_type.value, exc,
                )
                self._record_failure(module_name)
                self._update_weight(request_type.value, module_name, success=False)

        # التدهور البديل — Graceful degradation
        return await self.graceful_degradation(
            _FALLBACK_MAP.get(candidates[0] if candidates else "engine", [])
        )

    async def _dispatch_to_module(
        self,
        module_name: str,
        request_type: RequestType,
        data: Dict[str, Any],
    ) -> Any:
        """
        إرسال الطلب إلى موديول محدد — Dispatch request to a specific module.
        """
        module = getattr(self.engine, module_name, None)
        if module is None:
            raise RuntimeError(f"Module '{module_name}' not found on engine")

        # توجيه حسب نوع الطلب — Route based on request type
        if request_type == RequestType.CHAT:
            if hasattr(module, "chat"):
                return await module.chat(data.get("message", ""), **data)
            elif hasattr(module, "generate"):
                return await module.generate(data.get("message", ""))

        elif request_type == RequestType.CODE_GENERATION:
            if hasattr(module, "generate"):
                return await module.generate(data.get("prompt", ""))
            elif hasattr(module, "chat"):
                return await module.chat(data.get("prompt", ""))

        elif request_type == RequestType.RESEARCH:
            if hasattr(module, "search"):
                return await module.search(data.get("query", ""))
            elif hasattr(module, "retrieve"):
                return await module.retrieve(data.get("query", ""))

        elif request_type == RequestType.ANALYSIS:
            if hasattr(module, "analyze"):
                return await module.analyze(data)
            elif hasattr(module, "chat"):
                return await module.chat(str(data))

        elif request_type == RequestType.TOOL_EXECUTION:
            if hasattr(module, "execute"):
                return await module.execute(
                    data.get("tool_name", ""), data.get("params", {})
                )

        elif request_type == RequestType.SYSTEM:
            if hasattr(module, "get_diagnostics"):
                return await module.get_diagnostics()

        # محاولة عامة — Generic fallback
        if hasattr(module, "process"):
            return await module.process(data)
        if hasattr(module, "chat"):
            return await module.chat(str(data))

        raise RuntimeError(f"Module '{module_name}' has no compatible method for {request_type.value}")

    # ─────────────────────────────────────────────
    # صحة الموديولات / Module Health
    # ─────────────────────────────────────────────

    async def check_health(self) -> Dict[str, Any]:
        """
        فحص صحة جميع الموديولات — Check health of all modules.

        Returns / المخرجات:
            قاموس صحة الموديولات — Dict of module name → health status
        """
        # قائمة الموديولات المعروفة — Known modules
        module_names = [
            "memory", "ethics", "security_guard", "notebook",
            "knowledge", "eyes", "tools", "provider", "engine",
            "plugins", "subagents", "scheduler",
        ]

        results = {}
        for name in module_names:
            health = await self._check_single_module(name)
            results[name] = {
                "healthy": health.healthy,
                "latency_ms": health.latency_ms,
                "failure_count": health.failure_count,
                "last_check": health.last_check,
                "circuit_open": self._is_circuit_open(name),
            }

        overall = all(h["healthy"] and not h["circuit_open"] for h in results.values())
        return {
            "overall_healthy": overall,
            "modules": results,
            "checked_at": time.time(),
        }

    async def get_module_health(self, name: str) -> ModuleHealth:
        """
        الحصول على صحة موديول محدد — Get health for a specific module.

        Args / المعاملات:
            name: اسم الموديول — Module name

        Returns / المخرجات:
            حالة الصحة — ModuleHealth instance
        """
        return await self._check_single_module(name)

    async def _check_single_module(self, name: str) -> ModuleHealth:
        """
        فحص موديول واحد — Perform health check on a single module.
        """
        start = time.time()
        module = getattr(self.engine, name, None)

        if module is None:
            health = ModuleHealth(
                name=name,
                healthy=False,
                failure_count=999,
                latency_ms=0.0,
            )
        else:
            try:
                # محاولة ping — Try to ping the module
                if hasattr(module, "health_check"):
                    await asyncio.wait_for(module.health_check(), timeout=5.0)
                elif hasattr(module, "ping"):
                    await asyncio.wait_for(module.ping(), timeout=5.0)
                # إذا وُجد الموديول ولم يُعطَ خطأ، فهو سليم
                latency = (time.time() - start) * 1000
                health = ModuleHealth(
                    name=name,
                    healthy=True,
                    latency_ms=round(latency, 2),
                )
                # إعادة تعيين عداد الإخفاقات — Reset failure count
                existing = self._module_health.get(name)
                if existing:
                    health.failure_count = 0

            except Exception as exc:
                latency = (time.time() - start) * 1000
                existing = self._module_health.get(name)
                prev_failures = existing.failure_count if existing else 0
                health = ModuleHealth(
                    name=name,
                    healthy=False,
                    failure_count=prev_failures + 1,
                    latency_ms=round(latency, 2),
                )
                logger.warning("Health check failed for '%s': %s", name, exc)

        self._module_health[name] = health
        return health

    # ─────────────────────────────────────────────
    # قاطع الدائرة / Circuit Breaker
    # ─────────────────────────────────────────────

    def _is_circuit_open(self, module_name: str) -> bool:
        """
        هل قاطع الدائرة مفتوح؟ — Is the circuit breaker open for a module?
        """
        if not self._circuit_open.get(module_name, False):
            return False

        # فحص انتهاء مدة التعافي — Check if recovery time has elapsed
        opened_at = self._circuit_opened_at.get(module_name, 0)
        if time.time() - opened_at > self._cb_recovery:
            logger.info("Circuit breaker recovery for '%s' — half-open", module_name)
            self._circuit_open[module_name] = False
            return False

        return True

    def _record_failure(self, module_name: str) -> None:
        """
        تسجيل إخفاق — Record a module failure and potentially open circuit breaker.
        """
        health = self._module_health.get(module_name)
        count = (health.failure_count if health else 0) + 1

        if count >= self._cb_threshold:
            self._circuit_open[module_name] = True
            self._circuit_opened_at[module_name] = time.time()
            logger.warning(
                "Circuit breaker OPEN for '%s' after %d failures (recovery=%ds)",
                module_name, count, self._cb_recovery,
            )

    # ─────────────────────────────────────────────
    # سير العمل / Workflows
    # ─────────────────────────────────────────────

    async def execute_workflow(
        self,
        workflow_def: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        تنفيذ سير عمل متعدد الخطوات — Execute a multi-step workflow.

        Args / المعاملات:
            workflow_def: تعريف سير العمل — Workflow definition dict:
                {
                    "name": "workflow_name",
                    "steps": [
                        {"name": "step1", "module": "memory", "action": "search"},
                        {"name": "step2", "module": "engine", "action": "chat"},
                    ]
                }

        Returns / المخرجات:
            نتيجة سير العمل — Workflow result dict
        """
        steps = [
            WorkflowStep(
                name=s.get("name", f"step_{i}"),
                module=s["module"],
                action=s["action"],
            )
            for i, s in enumerate(workflow_def.get("steps", []))
        ]

        workflow = Workflow(
            name=workflow_def.get("name", "unnamed"),
            steps=steps,
        )
        self._workflows[workflow.id] = workflow

        logger.info("Starting workflow '%s' [%s] with %d steps", workflow.name, workflow.id[:8], len(steps))

        # نشر حدث بداية سير العمل — Publish workflow start event
        await self.event_bus.publish_data(
            "orchestrator.workflow.started",
            {"workflow_id": workflow.id, "name": workflow.name},
            priority=EventPriority.HIGH,
            source="master",
        )

        step_results = []

        for i, step in enumerate(steps):
            workflow.current_step = i
            step.status = "RUNNING"

            # تجاوز الموديولات المعطلة — Skip modules with open circuit breaker
            if self._is_circuit_open(step.module):
                step.status = "SKIPPED"
                step.error = f"Circuit breaker open for module '{step.module}'"
                logger.warning("Workflow step '%s' skipped — CB open for '%s'", step.name, step.module)
                continue

            try:
                result = await self._execute_step(step, step_results)
                step.status = "COMPLETED"
                step.result = result
                step_results.append(result)
            except Exception as exc:
                step.status = "FAILED"
                step.error = str(exc)
                self._record_failure(step.module)
                logger.error(
                    "Workflow step '%s' failed: %s", step.name, exc, exc_info=True,
                )

                # قرار: متابعة أم إيقاف؟ — Decision: continue or stop?
                if workflow_def.get("stop_on_failure", True):
                    workflow.status = "FAILED"
                    workflow.result = {"error": f"Step '{step.name}' failed: {exc}"}
                    break

        if workflow.status != "FAILED":
            workflow.status = "COMPLETED"
            workflow.result = {"step_results": step_results}

        # نشر حدث نهاية سير العمل — Publish workflow end event
        await self.event_bus.publish_data(
            "orchestrator.workflow.completed",
            {
                "workflow_id": workflow.id,
                "name": workflow.name,
                "status": workflow.status,
                "steps_completed": sum(1 for s in steps if s.status == "COMPLETED"),
                "steps_failed": sum(1 for s in steps if s.status == "FAILED"),
            },
            priority=EventPriority.HIGH,
            source="master",
        )

        return {
            "workflow_id": workflow.id,
            "name": workflow.name,
            "status": workflow.status,
            "steps": [
                {
                    "name": s.name,
                    "module": s.module,
                    "action": s.action,
                    "status": s.status,
                    "error": s.error,
                }
                for s in steps
            ],
            "result": workflow.result,
        }

    async def _execute_step(
        self,
        step: WorkflowStep,
        previous_results: List[Any],
    ) -> Any:
        """
        تنفيذ خطوة واحدة — Execute a single workflow step.
        """
        module = getattr(self.engine, step.module, None)
        if module is None:
            raise RuntimeError(f"Module '{step.module}' not found")

        # محاولة استدعاء الإجراء المحدد — Try to call the specified action
        handler = getattr(module, step.action, None)
        if handler is not None and callable(handler):
            if asyncio.iscoroutinefunction(handler):
                return await handler(*previous_results)
            return handler(*previous_results)

        # محاولة generic process — Try generic process
        if hasattr(module, "process"):
            return await module.process(previous_results)

        raise RuntimeError(f"Module '{step.module}' has no action '{step.action}'")

    # ─────────────────────────────────────────────
    # التعلم التكيفي / Adaptive Learning
    # ─────────────────────────────────────────────

    def _update_weight(self, request_type: str, module: str, success: bool) -> None:
        """
        تحديث أوزان التوجيه — Update routing weights based on success/failure.

        الخوارزمية / Algorithm:
          - نجاح: weight += 0.1 (حد أقصى 2.0)
          - فشل: weight -= 0.2 (حد أدنى -1.0)
        """
        weights = self._routing_weights.setdefault(request_type, {})
        current = weights.get(module, 1.0)
        if success:
            weights[module] = min(current + 0.1, 2.0)
        else:
            weights[module] = max(current - 0.2, -1.0)

    async def learn_from_pattern(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        التعلم من نمط حدث — Learn from an event pattern to improve routing.

        يُستخدم لتحسين توجيه الطلبات بناءً على الأنماط الملاحظة.
        Used to improve request routing based on observed patterns.

        Args / المعاملات:
            event_type: نوع الحدث — Event type (e.g., "route_success", "route_failure")
            data: بيانات الحدث — Event data (should include "module", "request_type")
        """
        module = data.get("module", "")
        request_type = data.get("request_type", "")

        if not module or not request_type:
            return

        if event_type == "route_success":
            self._update_weight(request_type, module, success=True)
        elif event_type == "route_failure":
            self._update_weight(request_type, module, success=False)

        logger.debug(
            "Pattern learned: %s → %s (weights: %s)",
            event_type, module,
            self._routing_weights.get(request_type, {}),
        )

    # ─────────────────────────────────────────────
    # التدهور البديل / Graceful Degradation
    # ─────────────────────────────────────────────

    async def graceful_degradation(
        self,
        fallback_modules: List[str],
    ) -> Dict[str, Any]:
        """
        التدهور البديل عند فشل الموديول — Fallback when primary modules fail.

        Args / المعاملات:
            fallback_modules: قائمة الموديولات البديلة — List of fallback modules

        Returns / المخرجات:
            نتيجة التدهور — Degradation result
        """
        if not fallback_modules:
            logger.error("All modules failed — no fallback available")
            return {
                "module": "none",
                "success": False,
                "result": None,
                "error": "All modules failed — graceful degradation exhausted",
            }

        for module_name in fallback_modules:
            if self._is_circuit_open(module_name):
                continue
            try:
                module = getattr(self.engine, module_name, None)
                if module is not None:
                    logger.info("Graceful degradation → using '%s'", module_name)
                    return {
                        "module": module_name,
                        "success": True,
                        "result": f"Degraded to {module_name}",
                        "degraded": True,
                    }
            except Exception as exc:
                logger.warning("Fallback module '%s' also failed: %s", module_name, exc)

        return {
            "module": "none",
            "success": False,
            "result": None,
            "error": "All fallback modules also failed",
        }

    # ─────────────────────────────────────────────
    # التشخيص / Diagnostics
    # ─────────────────────────────────────────────

    async def get_diagnostics(self) -> Dict[str, Any]:
        """
        تشخيص شامل للنظام — Comprehensive system diagnostics.

        Returns / المخرجات:
            قاموس تشخيصي شامل — Comprehensive diagnostic dict
        """
        health = await self.check_health()
        event_stats = await self.event_bus.get_stats()
        task_stats = await self.task_queue.get_stats()

        return {
            "master_orchestrator": {
                "running": self._running,
                "modules_monitored": len(self._module_health),
                "workflows_tracked": len(self._workflows),
                "circuit_breakers": {
                    name: {"open": self._circuit_open.get(name, False)}
                    for name in self._circuit_open
                },
                "routing_weights": self._routing_weights,
            },
            "health": health,
            "event_bus": event_stats,
            "task_queue": task_stats,
            "timestamp": time.time(),
        }

    # ─────────────────────────────────────────────
    # بدء/إيقاف / Start/Stop
    # ─────────────────────────────────────────────

    async def start(self) -> None:
        """
        بدء المنسق — Start the orchestrator (event bus, task queue, health monitor).
        """
        if self._running:
            logger.warning("MasterOrchestrator already running")
            return

        self._running = True

        # بدء ناقل الأحداث — Start event bus
        await self.event_bus.start()

        # بدء طابور المهام — Start task queue
        await self.task_queue.start()

        # اشتراك في أحداث التوجيه — Subscribe to routing events for learning
        self._event_sub_id = await self.event_bus.subscribe(
            "orchestrator.*",
            self._on_orchestrator_event,
        )

        # بدء مراقبة الصحة — Start health monitoring
        self._health_task = asyncio.create_task(
            self._health_monitor_loop(),
            name="master-health-monitor",
        )

        logger.info("MasterOrchestrator started — monitoring %d modules", len(_DEFAULT_ROUTE_MAP))

    async def _on_orchestrator_event(self, event: Event) -> None:
        """
        معالج أحداث المنسق — Handle orchestrator events for adaptive learning.
        """
        await self.learn_from_pattern(event.topic.split(".")[-1], event.data or {})

    async def _health_monitor_loop(self) -> None:
        """
        حلقة مراقبة الصحة — Background health monitoring loop.
        """
        while self._running:
            try:
                await self.check_health()
            except Exception as exc:
                logger.error("Health monitor error: %s", exc, exc_info=True)

            await asyncio.sleep(self._health_check_interval)

    async def stop(self) -> None:
        """
        إيقاف المنسق تدريجياً — Graceful shutdown.
        """
        logger.info("MasterOrchestrator stopping...")
        self._running = False

        # إلغاء مراقبة الصحة — Cancel health monitor
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

        # إلغاء اشتراك الأحداث — Unsubscribe from events
        if self._event_sub_id:
            await self.event_bus.unsubscribe(self._event_sub_id)

        # إيقاف المكونات — Stop components
        await self.task_queue.stop()
        await self.event_bus.flush()

        logger.info("MasterOrchestrator stopped")
