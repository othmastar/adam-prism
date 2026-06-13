"""
Adam Prism Engine Utils - الأدوات المساعدة
==========================================
Utility methods: classify, security, generate wrapper, heal, verify, call wrappers, status
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

import httpx

from adam.engine.base import AdamPrismEngineBase

logger = logging.getLogger("adam_prism.core")


class AdamPrismEngineUtils(AdamPrismEngineBase):
    """
    Mixin with utility methods for the engine.
    """

    async def _extract_and_save_lessons(self, user_message: str, response_text: str, intent: dict):
        """استخلاص دروس من المحادثة وحفظها (بدون Ollama — كلمات مفتاحية فقط)"""
        if not self.notebook or not hasattr(self.notebook, 'update_user_profile'):
            return
        if not response_text.strip() or len(user_message) < 3:
            return

        try:
            msg_lower = user_message.lower()
            keywords = {
                "communication_style": ["أنا", "طريقتي", "أسلوبي", "أفضل", "احب", "أكره", "I like", "I prefer", "my style"],
                "preferences": ["أريد", "ابغى", "أحتاج", "need", "want", "require", "أفضل", "يفضل"],
                "thinking_patterns": ["أعتقد", "على ما يبدو", "ربما", "think", "maybe", "perhaps", "believe"],
                "interests": ["مهتم", "interests", "interested", "شغوف", "هوايتي", "hobby"],
                "personality_traits": ["أنا شخص", "طبيعتي", "شخصيتي", "my personality", "I am", "I'm"],
            }
            for section, words in keywords.items():
                if any(w in msg_lower for w in words):
                    key = f"keyword_{section}"
                    value = user_message[:100]
                    await self.notebook.update_user_profile(section, {key: value})
                    logger.info(f"📝 درس مستفاد: {section}")
                    break
        except Exception as e:
            logger.debug(f"تعذر استخلاص درس: {e}")

    def _quick_classify_intent(self, message: str) -> dict[str, Any]:
        """تصنيف سريع بدون Ollama — كلمات مفتاحية فقط"""
        msg = message.lower()
        keywords = {
            "strategic_analyst": ["منظومة", "architecture", "معماري", "شامل", "كامل", "نظرة عامة", "استراتيجية", "خطط", "roadmap", "مستقبل"],
            "technical_researcher": ["ابحث", "بحث", "معلومة", "معلومات", "ما هو", "ما هي", "إزاي", "كيف", "explain", "what is", "tell me about", "research"],
            "software_dev": ["ابني", "build", "create", "اصنع", "طور", "طورلي", "اكتب كود", "code", "برمجة", "برنامج", "function", "class"],
            "pen_tester": ["اختراق", "ثغرة", "vulnerability", "هجوم", "استغلال", "CVE", "exploit", "penetration", "red team", "ethical hack"],
            "systems_analyst": ["حلل", "تحليل", "بنية تحتية", "شبكة", "system", "infrastructure", "network", "سيرفر", "server", "قارن", "compare"],
            "knowledge_manager": ["doc", "document", "صنف", "classify", "نظم", "organize", "قارن", "لخص", "summary", "توثيق"],
            "teacher": ["اشرح", "شرح", "تعليم", "مبتدئ", "درس", "علمني", "فهم", "بساطة", "beginner", "tutorial"],
        }
        scores = {}
        for mode, words in keywords.items():
            scores[mode] = sum(1 for w in words if w in msg)

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            best = "teacher"
        return {"mode": best, "intent_type": "general", "confidence": 1.0, "topics": []}

    async def _security_check_with_timeout(self, message: str) -> dict:
        """فحص الأمان مع timeout"""
        try:
            result = await asyncio.wait_for(
                self.security.check(message), timeout=5
            )
            if result is None:
                return {"allowed": True, "reason": "no_security_module"}
            return result
        except asyncio.TimeoutError:
            # [M2] Fail-closed: timeout must deny, not allow
            return {"allowed": False, "reason": "security_check_timeout"}
        except Exception as e:
            logger.exception("Security check error:")
            # [M2] Fail-closed: errors must deny, not allow
            return {"allowed": False, "reason": f"security_check_error:{e}"}

    async def _generate_with_timeout(self, message: str, context: dict, deadline: float) -> str:
        """توليد مع deadline مطلق للمسار بالكامل"""
        remaining = max(5, deadline - time.time())
        return await asyncio.wait_for(
            self._generate(message, context), timeout=remaining
        )

    def _trim_conversation_history(self, max_size: int = 50):
        """قص تاريخ المحادثة لمنع تسرب الذاكرة"""
        if max_size <= 0 or len(self.conversation_history) <= max_size:
            return
        self.conversation_history = self.conversation_history[-max_size:]

    async def _heal_failed_subsystem(self, name: str) -> str | None:
        """محاولة إصلاح موديول معين — يرجع رسالة الإصلاح أو None لو ناجح"""
        try:
            if name == "ollama_base":
                ollama = self.provider._providers.get("ollama") if hasattr(self.provider, '_providers') else None
                if ollama and not ollama.base_url:
                    ollama.base_url = self.config.get("ollama_base", "http://localhost:11434")
                    return "Ollama base reset to default"
            if getattr(self, name, None) is None:
                self._init_stubs()
                if getattr(self, name, None) is not None:
                    return f"{name} initialized (stub)"
            if name == "memory" and self.memory is None:
                from core.memory import MemorySystem
                self.memory = MemorySystem(config=self.config.get("memory", {}))
                return "Memory re-initialized" if self.memory else None
            if name == "ethics" and self.ethics is None:
                from adam.ethics.gate import EthicsGate
                self.ethics = EthicsGate(config=self.config.get("ethics", {}))
                return "Ethics gate re-initialized" if self.ethics else None
            if name == "tools" and self.tools is None:
                from adam.tools.manager import ToolManager
                self.tools = ToolManager(config=self.config)
                return "Tools re-initialized" if self.tools else None
            if name == "notebook" and self.notebook is None:
                from core.notebook import NotebookEngine
                self.notebook = NotebookEngine(config=self.config.get("notebook", {}))
                return "Notebook re-initialized" if self.notebook else None
            if name == "trace_recorder" and self.trace_recorder is None:
                from core.trace_recorder import TraceRecorder
                self.trace_recorder = TraceRecorder()
                return "Trace recorder re-initialized" if self.trace_recorder else None
            if name == "eyes":
                if not self.eyes:
                    return None
                if hasattr(self.eyes, 'is_healthy'):
                    try:
                        healthy = await asyncio.wait_for(self.eyes.is_healthy(), timeout=10)
                        if not healthy:
                            await self.eyes.restart()
                            return "Browser restarted"
                    except TimeoutError:
                        await self.eyes.restart()
                        return "Browser restarted (timeout)"
            return None
        except Exception:
            logger.exception("تعذر إصلاح {name}:")
            return None

    def _self_verify_response(self, response: str, user_message: str, intent: dict) -> str:
        """تحقق ذاتي من جودة الرد قبل إرساله — قواعد بسيطة بدون استدعاء موديل"""
        if not response or not response.strip():
            return "مش فاهم طلبك — وضح أكتر."

        identity_violations = ["كمساعد", "كـ", "as an ai", "as a language model", "كـ llm", "as an assistant"]
        for v in identity_violations:
            if v in response.lower():
                response = response.replace(v, "").strip()
                break

        if len(response) > 3000 and len(user_message) < 50:
            response = response[:2000]
            for punct in [".", "!", "؟", "\n"]:
                last = response.rfind(punct)
                if last > 50:
                    response = response[:last + 1]
                    break

        has_tool = '"_tool"' in response
        practical_keywords = ["اعمل", "ابحث", "افتح", "شوف", "حمل", "نفذ", "execute", "search", "write", "read"]
        is_practical = any(kw in user_message.lower() for kw in practical_keywords)
        if is_practical and not has_tool and len(response) < 300:
            response += "\n\nعاوزني أنفذلك الحاجة دي بأداة من أدواتي؟"

        return response

    async def _call_ollama(self, prompt: str, system: str = "", timeout: float = 60.0) -> str:
        """استدعاء provider.generate (قديم — بقى wrapper)"""
        start = time.time()
        try:
            result = await self.provider.generate(prompt, system, timeout)
            self.metrics.timing("ollama.generate", (time.time() - start) * 1000)
            self.metrics.inc("ollama.generate_calls")
            return result
        except Exception:
            self.metrics.error("ollama.generate")
            raise

    async def _call_ollama_chat(self, messages: list[dict]) -> str:
        """استدعاء provider.chat (قديم — بقى wrapper)"""
        start = time.time()
        try:
            result = await self.provider.chat(messages)
            self.metrics.timing("ollama.chat", (time.time() - start) * 1000)
            self.metrics.inc("ollama.chat_calls")
            return result
        except Exception:
            self.metrics.error("ollama.chat")
            raise

    def _truncate_messages_for_lora(self, messages: list[dict], max_chars: int = 8000) -> list[dict]:
        """تقليم محتوى الرسائل مع الحفاظ على بنية conversation: system + user + assistant + user ..."""
        if not messages:
            return messages

        result = [messages[0]]
        total = len(messages[0].get("content", ""))

        remaining = messages[1:]
        # نضمن أول رسالة بعد system تكون user (Gemma 4 apply_chat_template)
        if len(remaining) > 6:
            tail = remaining[-6:]
            # لو أول رسالة مش user، نوسع النطاق عشان نجيب user قبلها
            if tail and tail[0].get("role") != "user":
                tail = remaining[-7:]
            remaining = tail
        elif len(remaining) > 4:
            tail = remaining[-4:]
            if tail and tail[0].get("role") != "user":
                tail = remaining[-5:]
            remaining = tail

        for m in remaining:
            content = m.get("content", "")
            free = max_chars - total
            if free <= 0:
                break
            if len(content) > free - 50:
                cut = content[:free - 100] + "\n...[truncated]"
                result.append({"role": m["role"], "content": cut})
            else:
                result.append(m)
                total += len(content)

        return result

    async def _call_lora_server(self, messages: list[dict]) -> str:
        """استدعاء LoRA server مع manual retry (async-safe)"""
        import logging as _log
        start = time.time()
        last_exc = None
        messages = self._truncate_messages_for_lora(messages, max_chars=10000)

        for attempt in range(1, 4):
            try:
                sys_len = len(messages[0].get("content", "")) if messages else 0
                user_msg = messages[-1].get("content", "") if len(messages) > 1 else ""
                _log.getLogger("adam_prism.core").info(f"LoRA call: sys_{sys_len}c user='{user_msg}' (attempt {attempt})")
                c = await self.shared_clients.get("lora", self.lora_server_url.rstrip('/'), timeout=180.0)
                r = await c.post(
                    "/chat",
                    json={"messages": messages}
                )
                r.raise_for_status()
                resp_text = r.json().get("response", "")
                _log.getLogger("adam_prism.core").info(f"LoRA resp: {len(resp_text)}c starts with '{resp_text[:150]}'")
                self.metrics.timing("ollama.chat", (time.time() - start) * 1000)
                self.metrics.inc("ollama.chat_calls")
                return resp_text
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError,
                    ConnectionError, TimeoutError) as e:
                last_exc = e
                if attempt < 3:
                    delay = min(0.5 * (2 ** (attempt - 1)), 10.0)
                    _log.getLogger("adam_prism.core").warning(
                        f"LoRA attempt {attempt} failed: {e}. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)

        self.metrics.error("ollama.chat")
        raise last_exc or RuntimeError("LoRA server call failed")

    def set_inference_mode(self, mode: str, lora_url: str | None = None):
        """تغيير وضع الاستدلال في وقت التشغيل"""
        if mode in ("ollama", "lora", "openai", "anthropic"):
            self.provider.set_mode(mode)
            self._inference_mode = mode
            if lora_url:
                self.lora_server_url = lora_url
            logger.info(f"🔄 تغيير وضع الاستدلال إلى: {mode}")

    async def get_status(self) -> dict[str, Any]:
        """حالة النظام الكاملة"""
        p = self.provider
        current_provider = p.current if p and hasattr(p, "current") else None
        return {
            "session_id": self.session_id,
            "model": current_provider.model if current_provider else "unknown",
            "inference_mode": p.mode if p else "unknown",
            "lora_server_url": self.lora_server_url,
            "active_mode": self.active_mode,
            "cycle_count": self.cycle_count,
            "conversation_length": len(self.conversation_history),
            "provider": p.mode if p else "unknown",
            "ollama_base": p._providers.get("ollama").base_url if p and "ollama" in p._providers else None,
            "openai_model": p._providers.get("openai").model if p and "openai" in p._providers else None,
            "anthropic_model": p._providers.get("anthropic").model if p and "anthropic" in p._providers else None,
            "modules_attached": {
                "memory": self.memory is not None,
                "ethics": self.ethics is not None,
                "security": self.security is not None,
                "notebook": self.notebook is not None,
                "knowledge": self.knowledge is not None,
                "eyes": self.eyes is not None,
                "tools": self.tools is not None,
                "pipeline": self.pipeline is not None,
                "trace_recorder": self.trace_recorder is not None,
                "scheduler": self.scheduler is not None,
                "plugins": self.plugins is not None,
                "subagents": self.subagents is not None,
                "platform_discord": self.platform_discord is not None,
                "meta_learner": self.meta_learner is not None
            },
            "scheduled_jobs": len(self.scheduler.list_jobs()) if self.scheduler else 0,
            "plugin_count": len(self.plugins.list_plugins()) if self.plugins else 0,
            "subagent_count": len(self.subagents.list_sessions()) if self.subagents else 0,
            "platforms": {
                "discord": self.platform_discord.get_status() if self.platform_discord else {},
            },
            "trace_recorder": self.trace_recorder.get_stats() if self.trace_recorder else {},
            "timestamp": datetime.now().isoformat()
        }
