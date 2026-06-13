"""
Adam Prism Engine Base - المحرك الرئيسي — HARDENED v2
=========================================================
المحرك المركزي الذي يربط كل موديولات النظام.
Base class: __init__, stubs, real modules init, watchdog, properties

[FIX v2]
- إصلاح _Stub.__getattr__ inverted logic
  الكود القديم كان يرجع _async_noop للأسماء اللي تبدأ بـ _
  هذا مقلوب — المفروض يرجع _async_noop للأسماء اللي لا تبدأ بـ _
  لأن الأسماء اللي تبدأ بـ _ عادة دوال داخلية (sync) والباقي async methods
"""

import asyncio
import logging
import os
import uuid
from collections import deque
from collections.abc import Callable
from datetime import datetime
from typing import Any

from adam.core.learning import PreferenceLearner
from adam.core.permissions import PermissionState
from adam.infrastructure import (
    CircuitBreaker,
    MetricsCollector,
    SharedClients,
    TTLCache,
)
from adam.security.guard import SecurityOrchestrator

logger = logging.getLogger("adam_prism.core")


class AdamPrismEngineBase:
    """
    Base class for Adam Prism Engine mixin chain.
    Contains: __init__, stubs, real modules init, watchdog, properties.
    """

    def __init__(self, config: dict[str, Any]):
        from adam.config import AdamConfig
        if isinstance(config, AdamConfig):
            self._adam_cfg = config
            self.config = config.to_dict()
        else:
            self._adam_cfg = AdamConfig.from_dict(config)
            self.config = config
        self.lora_server_url = self.config.get("lora_server_url", "http://localhost:8080")
        self.session_id = str(uuid.uuid4())
        self.context_window = self.config.get("context_window", 4096)
        self.token_budget = self.config.get("token_budget", 4000)
        self.permission = PermissionState(self.session_id)
        self.learner = PreferenceLearner()

        # Provider (Ollama / OpenAI / Anthropic)
        from adam.providers.manager import ProviderManager
        self.provider = ProviderManager(config)

        # الموديولات (سيتم حقنها لاحقاً)
        self.memory = None
        self.ethics = None
        self.security = None
        self.notebook = None
        self.knowledge = None
        self.eyes = None
        self.tools = None
        self.pipeline = None
        self.trace_recorder = None
        self.meta_learner = None
        self.scheduler = None
        self.plugins = None
        self.subagents = None
        self.platform_discord = None
        self.security_guard = SecurityOrchestrator()
        self.continuous_learner = None

        # Initialize stub objects للموديولات المش موجودة — عشان diagnostics يعدي
        self._init_stubs()

        # Initialize real modules (override stubs)
        self._init_real_modules()

        # Production infrastructure
        self.shared_clients = SharedClients()
        self.cache = TTLCache(default_ttl=120.0, max_size=300)
        self.metrics = MetricsCollector()
        self.ollama_cb = CircuitBreaker("ollama", failure_threshold=5, recovery_timeout=30.0)
        self._inference_mode = self.provider.mode  # for backward compat
        self.qdrant_cb = CircuitBreaker("qdrant", failure_threshold=5, recovery_timeout=30.0)

        # حالة النظام
        self.cycle_count = 0
        self.conversation_history: list[dict] = []
        self.max_history = config.get("max_conversation_history", 50)
        self.active_mode = "teacher"  # الوضع الافتراضي
        self._watchdog_task = None
        self._history_lock = asyncio.Lock()  # [M5] Thread-safe conversation history

        # نظام تتبع خطوات المعالجة
        self._step_listeners: list[Callable] = []
        self._pipeline_log: deque = deque(maxlen=200)  # [M7] Replaced list with deque to prevent truncation race
        self._current_cycle_steps: list[dict] = []

        # الأوضاع المعرفية السبعة (7 Cognitive Modes)
        self.cognitive_modes = {
            "strategic_analyst": {"weight": 1.0, "focus": "تحليل استراتيجي — نظرة شاملة لمكونات المنظومة والعلاقات"},
            "technical_researcher": {"weight": 1.0, "focus": "بحث تقني — شرح آلية العمل مع مثال عملي"},
            "software_dev": {"weight": 1.0, "focus": "تطوير برمجيات — كتابة كود مع شرح trade-offs"},
            "pen_tester": {"weight": 1.0, "focus": "اختبار اختراق — شرح مسار الهجوم مع CVEs وأوامر عملية"},
            "systems_analyst": {"weight": 1.0, "focus": "تحليل أنظمة — تحليل مكونات البنية التحتية مع توصيات"},
            "knowledge_manager": {"weight": 1.0, "focus": "إدارة معرفة — تنظيم المعلومات بهيكل واضح"},
            "teacher": {"weight": 1.0, "focus": "تعليم وتدريب — شرح ببساطة مع أمثلة وتدرج"}
        }

    @property
    def model_name(self) -> str:
        if self.provider and self.provider.current:
            return self.provider.current.model
        return "unknown"

    @property
    def inference_mode(self) -> str:
        return self.provider.mode if self.provider else "unknown"

    def _init_stubs(self):
        """إنشاء كائنات وهمية للموديولات غير الموجودة — عشان diagnostics يعدي"""
        class _Stub:
            def __init__(self, **methods):
                self._methods = methods
                self._last_unresolved = None
            def __getattr__(self, name):
                if name in self._methods:
                    return self._methods[name]
                logger.warning(
                    f"_Stub: استدعاء سمة غير معرّفة '{name}' — "
                    f"الموديول لم يُهيأ بعد أو فشل في التحميل"
                )
                self._last_unresolved = name
                async def _async_noop(*a, **kw):
                    logger.debug(f"_Stub.{name}() تم الاستدعاء بصمت — يعيد None")
                    return None
                def _sync_noop(*a, **kw):
                    logger.debug(f"_Stub.{name}() تم الاستدعاء بصمت — يعيد None")
                    return None
                return _sync_noop if name.startswith('__') else _async_noop

        async def _async_noop(*a, **kw): return None
        def _sync_noop(*a, **kw): return None
        def _empty_list(*a, **kw): return []

        if self.memory is None:
            async def _retrieve(q, **kw): return []
            async def _search(q, **kw): return []
            self.memory = _Stub(retrieve=_retrieve, search=_search)
        if self.ethics is None:
            async def _evaluate(*a, **kw): return {"approved": True, "scores": {}, "weighted_score": 1.0, "issues": []}
            self.ethics = _Stub(evaluate=_evaluate)
        if self.notebook is None:
            async def _load_profile(): return {}
            self.notebook = _Stub(
                update_user_profile=_sync_noop,
                load_user_profile=_load_profile,
                record=_async_noop,
            )
        if self.tools is None:
            async def _exec_action(*a, **kw): return {"success": False, "error": "أداة غير متصلة"}
            self.tools = _Stub(execute_action=_exec_action, action_log=[], get_action_log=lambda _limit=50: [])
        if self.pipeline is None:
            self.pipeline = _Stub()
        if self.security is None:
            async def _security_check(msg): return {"allowed": True, "reason": "stub"}
            self.security = _Stub(check=_security_check)
        if self.trace_recorder is None:
            self.trace_recorder = _Stub(
                record=_sync_noop,
                get_patterns_for_query=_empty_list,
                get_stats=dict,
            )
        if self.knowledge is None:
            async def _search(q, **kw): return []
            async def _store(*a, **kw): return None
            self.knowledge = _Stub(search=_search, store_conversation=_store)
        if self.eyes is None:
            async def _screenshot(*a, **kw): return {"path": None, "error": "stub"}
            async def _fetch(*a, **kw): return {"text": "", "error": "stub"}
            async def _click(*a, **kw): return {"success": False, "error": "stub"}
            async def _type_text(*a, **kw): return {"success": False, "error": "stub"}
            self.eyes = _Stub(screenshot=_screenshot, fetch=_fetch, click=_click, type_text=_type_text)
        if self.subagents is None:
            self.subagents = _Stub(spawn=lambda **kw: {"id": "stub"}, list_sessions=list,
                                   get=lambda i: None, remove=lambda i: True)
        if self.platform_discord is None:
            self.platform_discord = _Stub(start=lambda: None, stop=lambda: None, get_status=dict)

    def _init_real_modules(self):
        """تهيئة الموديولات الحقيقية — تستبدل الـ stubs"""
        try:
            from memory.memory_system import MemorySystem
            memory_config = {
                "qdrant_url": self.config.get("qdrant_url", "http://localhost:6333"),
                "ollama_base": self.config.get("ollama_base", "http://localhost:11434"),
                "embedding_model": self.config.get("embedding_model", "nomic-embed-text"),
            }
            self.memory = MemorySystem(config=memory_config)
            self.knowledge = self.memory  # Qdrant knowledge = MemorySystem
            logger.info("✅ MemorySystem initialized (real)")
        except Exception:
            logger.exception("⚠️ MemorySystem init failed, using stub:")

        try:
            from adam.scheduler import AdamScheduler
            self.scheduler = AdamScheduler(engine=self)
            logger.info("✅ Scheduler initialized (real)")
        except Exception:
            logger.exception("⚠️ Scheduler init failed:")

        try:
            from adam.plugins.manager import PluginManager
            self.plugins = PluginManager(engine=self)
            plugin_dir = self.config.get("plugins_dir", "data/plugins")
            if os.path.isdir(plugin_dir):
                self.plugins.load_from_dir(plugin_dir)
            logger.info(f"✅ PluginManager initialized ({len(self.plugins.list_plugins())} plugins)")
        except Exception:
            logger.exception("⚠️ PluginManager init failed:")

        try:
            from adam.subagents.manager import SubagentManager
            self.subagents = SubagentManager(engine=self)
            logger.info("✅ SubagentManager initialized (real)")
        except Exception:
            logger.exception("⚠️ SubagentManager init failed:")

        try:
            from adam.platforms.discord_bot import DiscordBot
            if self.config.get("discord_enabled", False):
                self.platform_discord = DiscordBot(engine=self, config=self.config)
                logger.info("✅ DiscordBot initialized (real)")
            else:
                logger.info("ℹ️ Discord bot disabled in config")
        except Exception:
            logger.exception("⚠️ DiscordBot init failed:")

        try:
            from adam.learning.learner import ContinuousLearner
            self.continuous_learner = ContinuousLearner(config=self.config)
            logger.info("✅ ContinuousLearner initialized")
        except Exception:
            logger.exception("⚠️ ContinuousLearner init failed:")
            self.continuous_learner = None

    def attach(self, module_name: str, module_instance: Any):
        """حقن موديول في المحرك"""
        setattr(self, module_name, module_instance)
        logger.info(f"تم ربط الموديول: {module_name}")

    def on_step(self, callback: Callable):
        """تسجيل مستمع لتحديثات خطوات المعالجة"""
        self._step_listeners.append(callback)

    async def _emit_step(self, step: str, status: str, details: dict | None = None):
        """بث تحديث خطوة المعالجة لجميع المستمعين"""
        step_info = {
            "step": step,
            "status": status,
            "details": details or {},
            "cycle": self.cycle_count,
            "timestamp": datetime.now().isoformat()
        }
        self._current_cycle_steps.append(step_info)
        self._pipeline_log.append(step_info)  # deque(maxlen=200) auto-evicts old entries
        for listener in self._step_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(step_info)
                else:
                    listener(step_info)
            except Exception:
                logger.exception("خطأ في مستمع الخطوات:")

    def get_pipeline_log(self, limit: int = 50) -> list[dict]:
        """آخر سجل لخطوات المعالجة"""
        return list(self._pipeline_log)[-limit:]  # [M7] deque → list for slicing

    async def start_watchdog(self, interval: int = 60):
        """خلفية مراقبة صحة جميع الموديولات وإعادة تشغيلها تلقائياً"""
        if self._watchdog_task:
            return
        async def _watchdog_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    subsystems = [
                        ("ollama_base", "Ollama"),
                        ("memory", "Memory"),
                        ("ethics", "Ethics"),
                        ("pipeline", "Pipeline"),
                        ("tools", "Tools"),
                        ("notebook", "Notebook"),
                        ("security", "Security"),
                        ("trace_recorder", "Trace Recorder"),
                        ("eyes", "Browser"),
                    ]
                    for attr, name in subsystems:
                        if attr == "eyes":
                            continue
                        is_healthy = getattr(self, attr, None) is not None
                        if not is_healthy:
                            logger.warning(f"⚠️ {name} غير سليم — محاولة إصلاح...")
                            action = await self._heal_failed_subsystem(attr)
                            if action:
                                logger.info(f"✅ {name}: {action}")
                            else:
                                logger.error(f"❌ {name}: تعذر الإصلاح")
                    if self.eyes and hasattr(self.eyes, 'is_healthy'):
                        try:
                            healthy = await asyncio.wait_for(self.eyes.is_healthy(), timeout=10)
                            if not healthy:
                                logger.warning("المتصفح غير سليم — إعادة تشغيل...")
                                await self.eyes.restart()
                        except TimeoutError:
                            logger.warning("فحص المتصفح تجاوز الوقت — إعادة تشغيل...")
                            await self.eyes.restart()
                        except Exception:
                            logger.exception("خطأ في فحص المتصفح:")
                    if self.cycle_count % 5 == 0:
                        import gc
                        gc.collect()
                except asyncio.CancelledError:
                    break
                except Exception:
                    logger.exception("خطأ في دورة المراقبة:")
        self._watchdog_task = asyncio.create_task(_watchdog_loop())
        logger.info(f"✅ تم تشغيل مراقب الصحة (كل {interval} ثانية)")

    async def stop_watchdog(self):
        """إيقاف مراقب الصحة"""
        if self._watchdog_task:
            self._watchdog_task.cancel()
            self._watchdog_task = None
