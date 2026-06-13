"""
Adam Prism — Master Orchestrator
====================================
المنسق المركزي الأعلى — يربط كل موديولات النظام وينسقها.
هذا هو "العقل" الذي يربط الذاكرة + الأمان + الأخلاق + الأدوات + التعلم + الوكلاء الفرعيين.

Master Orchestrator هو الطبقة التي تفتقدها كل المشاريع المنافسة:
- ليس مجرد router أو dispatcher
- يراقب صحة كل مكون ويقرر الاستجابة
- يتعلم من الأنماط ويحسّن التوجيه
- يضمن الاتساق بين الأنظمة المختلفة
- يدير دورة حياة المهام المعقدة

Features:
1. Intelligent Request Routing — توجيه ذكي حسب نوع الطلب
2. Cross-Module Coordination — تنسيق بين الموديولات
3. Health-Aware Load Balancing — توزيع مع مراعاة الصحة
4. Adaptive Learning — تعلم من الأنماط لتحسين التوجيه
5. Workflow Orchestration — سير عمل متعدد الخطوات
6. Graceful Degradation — تدهور سلس عند فشل المكونات
7. Circuit Breaker Integration — حماية من الأعطال المتتالية
8. Event-Driven Architecture — بنية مبنية على الأحداث
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from adam.orchestrator.event_bus import EventBus, Event, EventPriority
from adam.orchestrator.task_queue import TaskQueue, TaskPriority

logger = logging.getLogger("adam_prism.orchestrator")


# ═══════════════════════════════════════════════════════
# 1. Request Types & Routing
# ═══════════════════════════════════════════════════════

class RequestType(str, Enum):
    """أنواع الطلبات — يحدد كيف يوجهها Master Orchestrator"""
    CHAT = "chat"                    # محادثة عادية
    CODE_GENERATION = "code_gen"      # كتابة كود
    RESEARCH = "research"            # بحث ومعرفة
    ANALYSIS = "analysis"            # تحليل بيانات أو نظام
    TOOL_EXECUTION = "tool_exec"     # تنفيذ أداة
    WORKFLOW = "workflow"            # سير عمل متعدد الخطوات
    LEARNING = "learning"            # تعلم وتدريب
    SYSTEM_ADMIN = "sys_admin"       # إدارة النظام
    SECURITY_SCAN = "security"       # فحص أمني
    VOICE = "voice"                  # صوت


class ModuleHealth(str, Enum):
    """حالة صحة الموديول"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class ModuleStatus:
    """حالة موديول كاملة"""
    name: str
    health: ModuleHealth = ModuleHealth.OFFLINE
    latency_ms: float = 0.0
    success_rate: float = 0.0
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    total_calls: int = 0
    total_failures: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """خطوة في سير عمل"""
    name: str
    module: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class Workflow:
    """سير عمل متعدد الخطوات"""
    name: str
    steps: List[WorkflowStep]
    workflow_id: str = ""
    status: str = "pending"
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MasterOrchestrator:
    """
    المنسق المركزي — يربط وينسق كل موديولات آدم بريزم

    المسؤوليات:
    1. توجيه الطلبات للمكون المناسب
    2. مراقبة صحة كل مكون
    3. تنسيق سير العمل المعقد
    4. التعلم من الأنماط لتحسين الأداء
    5. إدارة التدهور السلس
    6. بث الأحداث بين المكونات
    """

    def __init__(self, engine=None):
        self.engine = engine
        self.event_bus = EventBus(replay_buffer_size=200)
        self.task_queue = TaskQueue(max_concurrent=3)

        # Module health tracking
        self._module_status: Dict[str, ModuleStatus] = {}
        self._health_check_interval = 30  # seconds
        self._health_task: Optional[asyncio.Task] = None

        # Routing rules: request_type → list of (module_name, priority_weight)
        self._routing_table: Dict[str, List[tuple]] = {
            RequestType.CHAT: [("engine", 1.0), ("knowledge", 0.8), ("memory", 0.6)],
            RequestType.CODE_GENERATION: [("engine", 1.0), ("knowledge", 0.7), ("tools", 0.5)],
            RequestType.RESEARCH: [("knowledge", 1.0), ("engine", 0.8), ("tools", 0.6)],
            RequestType.ANALYSIS: [("engine", 1.0), ("knowledge", 0.8), ("tools", 0.7)],
            RequestType.TOOL_EXECUTION: [("tools", 1.0), ("engine", 0.5)],
            RequestType.WORKFLOW: [("orchestrator", 1.0)],
            RequestType.LEARNING: [("learning", 1.0), ("knowledge", 0.7), ("memory", 0.5)],
            RequestType.SYSTEM_ADMIN: [("tools", 1.0), ("security", 0.8)],
            RequestType.SECURITY_SCAN: [("security", 1.0), ("tools", 0.6)],
            RequestType.VOICE: [("voice", 1.0), ("engine", 0.7)],
        }

        # Adaptive learning: track routing success rates
        self._routing_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"success": 0, "failure": 0})
        self._pattern_memory: Dict[str, str] = {}  # pattern → best_module

        # Workflow execution
        self._active_workflows: Dict[str, Workflow] = {}

        # Graceful degradation: fallback chains
        self._fallback_chains: Dict[str, List[str]] = {
            "engine": ["engine", "provider_fallback", "stub_response"],
            "knowledge": ["knowledge", "memory", "engine_without_rag"],
            "tools": ["tools", "shell_only", "text_response"],
            "security": ["security", "guard_only", "allow_with_warning"],
            "voice": ["voice", "text_only"],
        }

        # Event subscriptions for internal coordination
        self._setup_internal_subscriptions()

        logger.info("MasterOrchestrator: initialized — ready to coordinate all modules")

    def _setup_internal_subscriptions(self):
        """إعداد اشتراكات الأحداث الداخلية"""
        self.event_bus.subscribe("module.health_change", self._on_health_change)
        self.event_bus.subscribe("module.error", self._on_module_error, replay=True)
        self.event_bus.subscribe("workflow.step_complete", self._on_step_complete)
        self.event_bus.subscribe("security.threat_detected", self._on_security_threat)

    # ═══════════════════════════════════════════════════════
    # 2. Lifecycle Management
    # ═══════════════════════════════════════════════════════

    async def start(self):
        """تشغيل المنسق وكل الأنظمة الفرعية"""
        logger.info("MasterOrchestrator: starting all subsystems...")
        await self.task_queue.start(num_workers=3)
        self.event_bus.start_workers()
        self._health_task = asyncio.create_task(self._health_monitor_loop())

        # Register all engine modules for health tracking
        if self.engine:
            for attr in ["memory", "ethics", "security", "notebook", "knowledge",
                         "eyes", "tools", "pipeline", "trace_recorder", "scheduler",
                         "plugins", "subagents", "security_guard", "continuous_learner"]:
                module = getattr(self.engine, attr, None)
                if module is not None:
                    self._module_status[attr] = ModuleStatus(
                        name=attr,
                        health=ModuleHealth.HEALTHY,
                    )

        logger.info("MasterOrchestrator: all subsystems started")

    async def stop(self):
        """إيقاف المنسق بشكل نظيف"""
        logger.info("MasterOrchestrator: stopping...")
        if self._health_task:
            self._health_task.cancel()
            self._health_task = None
        self.event_bus.stop_workers()
        await self.task_queue.stop()
        logger.info("MasterOrchestrator: stopped")

    # ═══════════════════════════════════════════════════════
    # 3. Intelligent Request Routing
    # ═══════════════════════════════════════════════════════

    def classify_request(self, message: str, context: Dict[str, Any] = None) -> RequestType:
        """
        تصنيف الطلب وتحديد نوعه — يحدد كيف يوجهه Master Orchestrator
        يستخدم كلمات مفتاحية + سياق + أنماط تعلم
        """
        msg = message.lower()
        context = context or {}

        # Check pattern memory first (adaptive learning)
        for pattern, req_type in self._pattern_memory.items():
            if pattern in msg:
                return RequestType(req_type)

        # Code generation patterns
        code_keywords = ["كود", "برمج", "اكتب", "function", "class", "import", "def ",
                         "build", "create", "develop", "code", "برنامج", "سكريبت", "script"]
        if any(kw in msg for kw in code_keywords):
            return RequestType.CODE_GENERATION

        # Research patterns
        research_keywords = ["ابحث", "بحث", "معلومة", "ما هو", "ما هي", "explain",
                             "what is", "tell me about", "research", "إزاي", "كيف"]
        if any(kw in msg for kw in research_keywords):
            return RequestType.RESEARCH

        # Analysis patterns
        analysis_keywords = ["حلل", "تحليل", "قارن", "compare", "analyze", "evaluate",
                             "بنية", "architecture", "system", "منظومة"]
        if any(kw in msg for kw in analysis_keywords):
            return RequestType.ANALYSIS

        # Tool execution patterns
        tool_keywords = ["نفذ", "افتح", "شغل", "execute", "run", "open", "install",
                         "تحميل", "download", "حذف", "delete"]
        if any(kw in msg for kw in tool_keywords):
            return RequestType.TOOL_EXECUTION

        # Security patterns
        security_keywords = ["فحص أمني", "ثغرة", "vulnerability", "security", "penetration",
                             "اختراق", "CVE", "exploit"]
        if any(kw in msg for kw in security_keywords):
            return RequestType.SECURITY_SCAN

        # System admin patterns
        admin_keywords = ["إعدادات", "settings", "config", "مفتاح", "key", "صلاحية",
                          "permission", "إدارة", "admin"]
        if any(kw in msg for kw in admin_keywords):
            return RequestType.SYSTEM_ADMIN

        # Workflow patterns
        workflow_keywords = ["خطوات", "سير عمل", "workflow", "pipeline", "اولاً ثم",
                             "خطة", "plan", "roadmap"]
        if any(kw in msg for kw in workflow_keywords):
            return RequestType.WORKFLOW

        # Default: chat
        return RequestType.CHAT

    def get_routing_plan(self, request_type: RequestType) -> List[Dict[str, Any]]:
        """
        يحدد خطة التوجيه — أي موديولات تشارك وبأي ترتيب
        يراعي حالة الصحة والأولويات
        """
        modules = self._routing_table.get(request_type, [("engine", 1.0)])
        plan = []
        for module_name, weight in modules:
            status = self._module_status.get(module_name, ModuleStatus(name=module_name))
            # Adjust weight based on health
            adjusted_weight = weight
            if status.health == ModuleHealth.DEGRADED:
                adjusted_weight *= 0.7
            elif status.health == ModuleHealth.UNHEALTHY:
                adjusted_weight *= 0.3
            elif status.health == ModuleHealth.OFFLINE:
                adjusted_weight *= 0.0
            # Adjust weight based on success rate
            if status.total_calls > 0:
                adjusted_weight *= (status.success_rate + 0.1)
            plan.append({
                "module": module_name,
                "weight": adjusted_weight,
                "health": status.health.value,
                "fallback_chain": self._fallback_chains.get(module_name, [module_name]),
            })
        # Sort by adjusted weight (highest first)
        plan.sort(key=lambda x: x["weight"], reverse=True)
        return plan

    async def route_request(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        توجيه طلب ذكي — القلب النابض لـ Master Orchestrator

        الخطوات:
        1. تصنيف الطلب
        2. بناء خطة التوجيه
        3. تنفيذ الخطة مع fallback
        4. تعلم من النتيجة
        5. بث الحدث
        """
        start_time = time.time()
        request_type = self.classify_request(message, context)
        plan = self.get_routing_plan(request_type)

        logger.info(f"MasterOrchestrator: routing '{request_type.value}' → {[p['module'] for p in plan]}")

        # Broadcast routing event
        self.event_bus.publish_sync(Event(
            topic="orchestrator.request_routed",
            data={"request_type": request_type.value, "plan": plan, "message_preview": message[:100]},
            source="god_orchestrator",
            priority=EventPriority.NORMAL,
        ))

        result = None
        errors = []
        modules_used = []

        for step in plan:
            module_name = step["module"]
            if step["weight"] <= 0:
                # Try fallback chain
                for fallback in step.get("fallback_chain", []):
                    fallback_status = self._module_status.get(fallback)
                    if fallback_status and fallback_status.health in (ModuleHealth.HEALTHY, ModuleHealth.DEGRADED):
                        module_name = fallback
                        break
                else:
                    continue

            try:
                result = await self._execute_on_module(module_name, message, context)
                if result:
                    modules_used.append(module_name)
                    self._record_routing_success(request_type.value, module_name)
                    break
            except Exception as e:
                errors.append(f"{module_name}: {e}")
                self._record_routing_failure(request_type.value, module_name)
                logger.warning(f"MasterOrchestrator: module '{module_name}' failed: {e}")
                continue

        # Learn from this routing decision
        if result and modules_used:
            self._learn_pattern(message, modules_used[0])

        duration_ms = (time.time() - start_time) * 1000

        # Broadcast completion event
        self.event_bus.publish_sync(Event(
            topic="orchestrator.request_completed",
            data={
                "request_type": request_type.value,
                "modules_used": modules_used,
                "duration_ms": duration_ms,
                "success": result is not None,
                "errors": errors,
            },
            source="god_orchestrator",
            priority=EventPriority.LOW,
        ))

        return {
            "result": result,
            "request_type": request_type.value,
            "modules_used": modules_used,
            "errors": errors,
            "duration_ms": duration_ms,
        }

    async def _execute_on_module(self, module_name: str, message: str,
                                  context: Dict[str, Any] = None) -> Optional[Any]:
        """تنفيذ على موديول محدد"""
        if not self.engine:
            return None

        context = context or {}
        status = self._module_status.get(module_name, ModuleStatus(name=module_name))
        status.total_calls += 1

        try:
            if module_name == "engine":
                result = await asyncio.wait_for(
                    self.engine.chat(message, context),
                    timeout=120.0
                )
                status.health = ModuleHealth.HEALTHY
                status.last_success = datetime.now(timezone.utc).isoformat()
                return result

            elif module_name == "knowledge" and self.engine.knowledge:
                results = await asyncio.wait_for(
                    self.engine.knowledge.search(message, top_k=5),
                    timeout=10.0
                )
                status.health = ModuleHealth.HEALTHY
                status.last_success = datetime.now(timezone.utc).isoformat()
                return {"knowledge_results": results}

            elif module_name == "tools" and self.engine.tools:
                # Delegate to engine's tool execution
                result = await asyncio.wait_for(
                    self.engine.chat(message, context),
                    timeout=60.0
                )
                status.health = ModuleHealth.HEALTHY
                status.last_success = datetime.now(timezone.utc).isoformat()
                return result

            elif module_name == "security" and self.engine.security_guard:
                verdict = await self.engine.security_guard.check_input(message)
                status.health = ModuleHealth.HEALTHY
                return {"security_verdict": verdict}

            elif module_name == "memory" and self.engine.memory:
                results = await self.engine.memory.search(message, top_k=3)
                status.health = ModuleHealth.HEALTHY
                return {"memory_results": results}

            else:
                # Fallback: use engine
                result = await asyncio.wait_for(
                    self.engine.chat(message, context),
                    timeout=120.0
                )
                return result

        except asyncio.TimeoutError:
            status.health = ModuleHealth.DEGRADED
            status.last_failure = datetime.now(timezone.utc).isoformat()
            raise TimeoutError(f"Module '{module_name}' timed out")
        except Exception as e:
            status.total_failures += 1
            if status.total_calls > 0:
                status.success_rate = 1.0 - (status.total_failures / status.total_calls)
            status.last_failure = datetime.now(timezone.utc).isoformat()
            if status.total_failures > 5:
                status.health = ModuleHealth.UNHEALTHY
            raise

    # ═══════════════════════════════════════════════════════
    # 4. Workflow Orchestration
    # ═══════════════════════════════════════════════════════

    async def execute_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """
        تنفيذ سير عمل متعدد الخطوات — مع تبعيات وإعادة محاولة
        """
        workflow.workflow_id = workflow.workflow_id or f"wf_{int(time.time())}"
        workflow.status = "running"
        self._active_workflows[workflow.workflow_id] = workflow

        logger.info(f"MasterOrchestrator: starting workflow '{workflow.name}' ({len(workflow.steps)} steps)")

        completed_steps: Set[str] = set()
        max_iterations = len(workflow.steps) * 2  # prevent infinite loops
        iteration = 0

        while len(completed_steps) < len(workflow.steps) and iteration < max_iterations:
            iteration += 1
            progress = False

            for step in workflow.steps:
                if step.name in completed_steps:
                    continue

                # Check dependencies
                if any(dep not in completed_steps for dep in step.depends_on):
                    continue

                # Execute step
                try:
                    step_result = await self._execute_workflow_step(step, workflow)
                    workflow.results[step.name] = step_result
                    completed_steps.add(step.name)
                    progress = True

                    self.event_bus.publish_sync(Event(
                        topic="workflow.step_complete",
                        data={"workflow_id": workflow.workflow_id, "step": step.name, "success": True},
                        source="god_orchestrator",
                        priority=EventPriority.NORMAL,
                    ))
                except Exception as e:
                    step.retry_count += 1
                    if step.retry_count > step.max_retries:
                        workflow.errors.append(f"Step '{step.name}' failed permanently: {e}")
                        completed_steps.add(step.name)  # Mark as done (failed)
                    else:
                        workflow.errors.append(f"Step '{step.name}' failed (attempt {step.retry_count}): {e}")
                    progress = True

            if not progress:
                await asyncio.sleep(0.1)

        workflow.status = "completed" if not workflow.errors else "completed_with_errors"
        logger.info(f"MasterOrchestrator: workflow '{workflow.name}' {workflow.status} "
                     f"({len(completed_steps)}/{len(workflow.steps)} steps)")

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status,
            "results": workflow.results,
            "errors": workflow.errors,
            "steps_completed": len(completed_steps),
            "steps_total": len(workflow.steps),
        }

    async def _execute_workflow_step(self, step: WorkflowStep, workflow: Workflow) -> Any:
        """تنفيذ خطوة واحدة في سير العمل"""
        # Pass results from previous steps as context
        context = {
            "workflow_id": workflow.workflow_id,
            "previous_results": workflow.results,
        }

        module_name = step.module
        if module_name == "orchestrator":
            # Recursive — execute as sub-workflow or direct action
            return await self._execute_on_module("engine", step.action, context)

        return await self._execute_on_module(module_name, step.action, context)

    # ═══════════════════════════════════════════════════════
    # 5. Health Monitoring
    # ═══════════════════════════════════════════════════════

    async def _health_monitor_loop(self):
        """مراقبة صحة الموديولات بشكل دوري"""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self.check_all_modules_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")

    async def check_all_modules_health(self):
        """فحص صحة كل الموديولات"""
        if not self.engine:
            return

        for attr in list(self._module_status.keys()):
            module = getattr(self.engine, attr, None)
            if module is None:
                status = self._module_status[attr]
                old_health = status.health
                status.health = ModuleHealth.OFFLINE
                if old_health != ModuleHealth.OFFLINE:
                    self.event_bus.publish_sync(Event(
                        topic="module.health_change",
                        data={"module": attr, "old_health": old_health.value, "new_health": "offline"},
                        source="god_orchestrator",
                        priority=EventPriority.HIGH,
                    ))
            else:
                # Simple health check: is the module responsive?
                status = self._module_status[attr]
                if status.total_calls > 0:
                    if status.success_rate >= 0.9:
                        new_health = ModuleHealth.HEALTHY
                    elif status.success_rate >= 0.5:
                        new_health = ModuleHealth.DEGRADED
                    else:
                        new_health = ModuleHealth.UNHEALTHY

                    if new_health != status.health:
                        old_health = status.health
                        status.health = new_health
                        self.event_bus.publish_sync(Event(
                            topic="module.health_change",
                            data={"module": attr, "old_health": old_health.value, "new_health": new_health.value},
                            source="god_orchestrator",
                            priority=EventPriority.HIGH,
                        ))

    # ═══════════════════════════════════════════════════════
    # 6. Event Handlers
    # ═══════════════════════════════════════════════════════

    async def _on_health_change(self, event: Event):
        """معالجة تغير حالة الصحة"""
        data = event.data
        module = data.get("module", "unknown")
        new_health = data.get("new_health", "unknown")
        logger.info(f"MasterOrchestrator: module '{module}' health changed to '{new_health}'")

        if new_health in ("unhealthy", "offline"):
            # Try to heal the module
            if self.engine and hasattr(self.engine, '_heal_failed_subsystem'):
                try:
                    action = await asyncio.wait_for(
                        self.engine._heal_failed_subsystem(module),
                        timeout=30.0
                    )
                    if action:
                        logger.info(f"MasterOrchestrator: healed '{module}': {action}")
                except Exception as e:
                    logger.warning(f"MasterOrchestrator: failed to heal '{module}': {e}")

    async def _on_module_error(self, event: Event):
        """معالجة خطأ في موديول"""
        data = event.data
        module = data.get("module", "unknown")
        error = data.get("error", "unknown")
        logger.warning(f"MasterOrchestrator: module '{module}' error: {error}")

        # Update module status
        status = self._module_status.get(module)
        if status:
            status.total_failures += 1
            status.last_failure = datetime.now(timezone.utc).isoformat()
            if status.total_calls > 0:
                status.success_rate = 1.0 - (status.total_failures / status.total_calls)

    async def _on_step_complete(self, event: Event):
        """معالجة إكمال خطوة في سير عمل"""
        data = event.data
        logger.debug(f"MasterOrchestrator: workflow step '{data.get('step')}' completed")

    async def _on_security_threat(self, event: Event):
        """معالجة تهديد أمني"""
        data = event.data
        logger.critical(f"MasterOrchestrator: SECURITY THREAT: {data}")
        # Could trigger automatic responses: block IP, disable module, etc.

    # ═══════════════════════════════════════════════════════
    # 7. Adaptive Learning
    # ═══════════════════════════════════════════════════════

    def _record_routing_success(self, request_type: str, module: str):
        """تسجيل نجاح التوجيه"""
        key = f"{request_type}:{module}"
        self._routing_stats[key]["success"] += 1

    def _record_routing_failure(self, request_type: str, module: str):
        """تسجيل فشل التوجيه"""
        key = f"{request_type}:{module}"
        self._routing_stats[key]["failure"] += 1

    def _learn_pattern(self, message: str, best_module: str):
        """تعلم نمط — يربط كلمات مفتاحية بأفضل موديول"""
        msg_lower = message.lower()
        # Extract key phrases (2-3 word combinations)
        words = msg_lower.split()
        for i in range(len(words)):
            for length in (2, 3):
                if i + length <= len(words):
                    phrase = " ".join(words[i:i + length])
                    if len(phrase) >= 4:  # ignore very short patterns
                        self._pattern_memory[phrase] = best_module

        # Keep pattern memory bounded
        if len(self._pattern_memory) > 500:
            # Remove least used patterns (simple: keep first half)
            items = list(self._pattern_memory.items())
            self._pattern_memory = dict(items[:250])

    # ═══════════════════════════════════════════════════════
    # 8. Dashboard & Diagnostics
    # ═══════════════════════════════════════════════════════

    def get_dashboard(self) -> Dict[str, Any]:
        """لوحة تحكم شاملة — كل معلومات النظام في مكان واحد"""
        module_health = {}
        for name, status in self._module_status.items():
            module_health[name] = {
                "health": status.health.value,
                "success_rate": round(status.success_rate, 2),
                "total_calls": status.total_calls,
                "total_failures": status.total_failures,
                "last_success": status.last_success,
                "last_failure": status.last_failure,
            }

        return {
            "orchestrator": "MasterOrchestrator",
            "status": "running",
            "modules": module_health,
            "event_bus": self.event_bus.stats(),
            "task_queue": self.task_queue.stats(),
            "routing_patterns_learned": len(self._pattern_memory),
            "active_workflows": len(self._active_workflows),
            "routing_stats": dict(self._routing_stats),
        }

    def get_routing_suggestions(self) -> List[Dict[str, Any]]:
        """اقتراحات لتحسين التوجيه بناءً على الإحصائيات"""
        suggestions = []
        for key, stats in self._routing_stats.items():
            total = stats["success"] + stats["failure"]
            if total > 0:
                success_rate = stats["success"] / total
                if success_rate < 0.5:
                    suggestions.append({
                        "route": key,
                        "success_rate": round(success_rate, 2),
                        "recommendation": "Consider rerouting or checking module health",
                    })
        return suggestions

    async def diagnose(self) -> Dict[str, Any]:
        """تشخيص كامل للنظام — يفحص كل مكون ويقدم توصيات"""
        diagnosis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_health": "unknown",
            "modules": {},
            "issues": [],
            "recommendations": [],
        }

        healthy_count = 0
        total_count = len(self._module_status)

        for name, status in self._module_status.items():
            is_healthy = status.health in (ModuleHealth.HEALTHY, ModuleHealth.DEGRADED)
            if is_healthy:
                healthy_count += 1

            module_diag = {
                "health": status.health.value,
                "success_rate": round(status.success_rate, 2),
                "issues": [],
            }

            if status.health == ModuleHealth.UNHEALTHY:
                module_diag["issues"].append("Module is unhealthy — high failure rate")
                diagnosis["issues"].append(f"Module '{name}' is unhealthy")
                diagnosis["recommendations"].append(f"Check and restart module '{name}'")

            if status.health == ModuleHealth.OFFLINE:
                module_diag["issues"].append("Module is offline")
                diagnosis["issues"].append(f"Module '{name}' is offline")

            if status.success_rate < 0.7 and status.total_calls > 5:
                module_diag["issues"].append(f"Low success rate: {status.success_rate:.0%}")
                diagnosis["recommendations"].append(f"Investigate failures in '{name}'")

            diagnosis["modules"][name] = module_diag

        # Overall health
        if total_count > 0:
            health_ratio = healthy_count / total_count
            if health_ratio >= 0.8:
                diagnosis["overall_health"] = "healthy"
            elif health_ratio >= 0.5:
                diagnosis["overall_health"] = "degraded"
            else:
                diagnosis["overall_health"] = "critical"

        # Add routing suggestions
        routing_suggestions = self.get_routing_suggestions()
        if routing_suggestions:
            diagnosis["recommendations"].extend(
                [f"Routing: {s['route']} has {s['success_rate']:.0%} success — {s['recommendation']}"
                 for s in routing_suggestions]
            )

        return diagnosis
