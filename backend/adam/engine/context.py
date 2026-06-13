"""
Adam Prism Engine Context - بناء السياق
========================================
Build context with intelligent collection routing (RAG)
"""

import logging

from adam.engine.utils import AdamPrismEngineUtils

logger = logging.getLogger("adam_prism.core")


class AdamPrismEngineContext(AdamPrismEngineUtils):
    """
    Mixin: context building with RAG collection routing.
    """

    async def _build_context(self, message: str, intent: dict) -> dict:
        """بناء السياق + RAG ذكي: يدور في الكوليكشن المناسب حسب intent"""
        context = {
            "intent": intent,
            "mode": self.active_mode,
            "cycle": self.cycle_count,
            "recent_conversation": self.conversation_history[-10:] if self.max_history > 0 else []
        }

        intent_type = intent.get("intent_type", "general").lower()
        topics = " ".join(intent.get("topics", []))
        combined_query = f"{message} {topics}".strip()

        if self.memory:
            relevant_memories = await self.memory.retrieve(combined_query, top_k=3)
            context["memories"] = relevant_memories

            try:
                arch = await self.memory.search(combined_query, collection="project_architecture", top_k=3)
                if arch: context["project_arch"] = arch
            except Exception as e:
                logger.debug(f"search project_architecture: {e}")

            try:
                profile = await self.memory.search(combined_query, collection="user_profile", top_k=3)
                if profile: context["user_profile_kb"] = profile
            except Exception as e:
                logger.debug(f"search user_profile: {e}")

            try:
                conv = await self.memory.search(combined_query, collection="conversation_memory", top_k=3)
                if conv: context["conv_memory"] = conv
            except Exception as e:
                logger.debug(f"search conversation_memory: {e}")

            fe_keywords = ["frontend", "ui", "component", "store", "zustand", "nextjs", "next.js",
                          "react", "tailwind", "shadcn", "page", "layout", "chat-interface", "sidebar",
                          "button", "card", "dialog", "form", "واجهة", "فرونت", "component"]
            if any(kw in combined_query.lower() for kw in fe_keywords) or intent_type in ("software_dev", "technical_researcher"):
                try:
                    fe = await self.memory.search(combined_query, collection="frontend_components", top_k=3)
                    if fe: context["frontend_kb"] = fe
                except Exception as e:
                    logger.debug(f"search frontend_components: {e}")

            be_keywords = ["backend", "engine", "memory", "security", "ethics", "notebook", "pipeline",
                          "api", "tool", "module", "class", "function", "server", "python", "fastapi",
                          "باكل", "باك", "محرك", "أمان", "ذاكرة", "أداة"]
            if any(kw in combined_query.lower() for kw in be_keywords) or intent_type in ("systems_analyst",):
                try:
                    be = await self.memory.search(combined_query, collection="backend_modules", top_k=3)
                    if be: context["backend_kb"] = be
                except Exception as e:
                    logger.debug(f"search backend_modules: {e}")

            tool_keywords = ["tool", "execute", "browser_", "mouse_", "keyboard_", "file_", "screenshot",
                           "clipboard", "search_knowledge", "scrapling", "استعمل", "نفذ", "شغل",
                           "أداة", "اعمل", "افتح", "ابحث", "حمل"]
            if any(kw in combined_query.lower() for kw in tool_keywords) or '"tool"' in combined_query or '"_tool"' in combined_query:
                try:
                    td = await self.memory.search(combined_query, collection="tools_docs", top_k=3)
                    if td: context["tools_kb"] = td
                except Exception as e:
                    logger.debug(f"search tools_docs: {e}")

            sec_keywords = ["security", "injection", "pii", "jailbreak", "hack", "exploit", "cve",
                           "vuln", "guard", "shield", "firewall", "pentest", "اختراق", "أمان",
                           "ثغرة", "هجوم", "حماية",
                           "fintech", "finance", "bank", "payment", "سند", "صك", "صكوك", "بنك",
                           "تمويل", "مدفوعات", "رقمية", "مصرفي", "تكافل", "إسلامي",
                           "ceo", "leadership", "قيادة", "حوكمة", "إدارة", "استراتيجي",
                           "mudarabah", "musharakah", "sukuk", "takaful", "murabaha"]
            if any(kw in combined_query.lower() for kw in sec_keywords) or intent_type in ("pen_tester",):
                try:
                    sec = await self.memory.search(combined_query, collection="security_guard", top_k=3)
                    if sec: context["security_kb"] = sec
                except Exception as e:
                    logger.debug(f"search security_guard: {e}")

            dep_keywords = ["docker", "deploy", "compose", "container", "volume", "port", "config",
                           "install", "setup", "start", "run", "server", "nginx", "uvicorn",
                           "نشر", "تشغيل", "تثبيت", "إعدادات"]
            if any(kw in combined_query.lower() for kw in dep_keywords):
                try:
                    dep = await self.memory.search(combined_query, collection="deployment_infra", top_k=3)
                    if dep: context["deploy_kb"] = dep
                except Exception as e:
                    logger.debug(f"search deployment_infra: {e}")

            if not any(context.get(k) for k in ["project_arch", "user_profile_kb", "conv_memory",
                "frontend_kb", "backend_kb", "tools_kb", "security_kb", "deploy_kb"]):
                try:
                    fallback = await self.memory.search(combined_query, collection="project_architecture", top_k=3)
                    if fallback: context["fallback_kb"] = fallback
                except Exception as e:
                    logger.debug(f"search fallback: {e}")

        if self.trace_recorder:
            patterns = self.trace_recorder.get_patterns_for_query(
                message, intent.get("intent_type", "general"), max_results=3
            )
            if patterns:
                context["patterns"] = patterns

        if self.notebook and hasattr(self.notebook, 'load_user_profile'):
            try:
                profile = await self.notebook.load_user_profile()
                if profile:
                    context["user_profile"] = profile
            except Exception:
                logger.exception("تعذر تحميل ملف المستخدم:")

        return context
