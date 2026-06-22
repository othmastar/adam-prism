"""
Adam Prism — Unified Memory Manager
=====================================
مدير الذاكرة الموحد — يدمج 4 طبقات ذاكرة في واجهة واحدة.
مستوحى من Hermes Agent — "Four-Layer Memory System".

الطبقات:
1. Hot Memory (MEMORY.md/USER.md) — دايماً في system prompt
2. Session Search (FTS5) — بحث نصي كامل في كل الجلسات
3. Skills (Procedural Memory) — إجراءات قابلة لإعادة الاستخدام
4. Vector Memory (Qdrant + SQLite) — ذاكرة دلالية + مهيكلة

الميزات الفريدة:
- Unified query: يبحث في كل الطبقات مرة واحدة
- Frozen snapshot: الطبقة 1 تُحمّل مرة واحدة بالجلسة
- Cross-layer insights: يربط النتائج من طبقات مختلفة
- Smart routing: يوجه الاستعلام للطبقة المناسبة تلقائياً
"""

import logging

from adam.memory.hot_memory import HotMemory
from adam.memory.session_search import SessionSearch

logger = logging.getLogger("adam_prism.memory.unified")

class UnifiedMemoryManager:
    """
    مدير الذاكرة الموحد — 4 طبقات ذاكرة.

    الواجهة الوحيدة التي يجب أن يستخدمها المحرك.
    ينسق بين كل الطبقات ويقدم بحث موحد.
    """

    def __init__(self, config: dict = None, vector_memory=None, skill_manager=None):
        cfg = config or {}

        # الطبقة 1: Hot Memory (MEMORY.md/USER.md)
        self.hot = HotMemory(config=cfg.get("hot_memory", {}))

        # الطبقة 2: Session Search (FTS5)
        self.session_search = SessionSearch(config=cfg.get("session_search", {}))

        # الطبقة 3: Skills (Procedural Memory) — يُحقن من الخارج
        self.skill_manager = skill_manager

        # الطبقة 4: Vector Memory (Qdrant + SQLite) — يُحقن من الخارج
        self.vector = vector_memory

        # إعدادات
        self.session_id = cfg.get("session_id", "default")
        self.nudge_interval = cfg.get("nudge_interval", 10)  # كل 10 أدوار
        self._turn_count = 0
        self._last_nudge = 0

    # ─── تهيئة الجلسة ────────────────────────────────

    async def start_session(self, session_id: str, platform: str = "cli",
                            model: str = "") -> dict:
        """
        بدء جلسة جديدة — تحميل snapshot + تسجيل الجلسة.
        يجب استدعاؤها في بداية كل جلسة.
        """
        self.session_id = session_id
        self._turn_count = 0

        # تحميل hot memory snapshot (frozen)
        self.hot.refresh_snapshot()

        # إنشاء جلسة في session search
        self.session_search.create_session(
            session_id=session_id, platform=platform, model=model
        )

        hot_text, user_text = self.hot.load_snapshot()

        return {
            "session_id": session_id,
            "hot_memory_loaded": bool(hot_text or user_text),
            "hot_memory_chars": len(hot_text),
            "user_profile_chars": len(user_text),
            "snapshot_frozen": True,
        }

    async def end_session(self, summary: str = "", tags: str = ""):
        """إنهاء الجلسة"""
        self.session_search.end_session(
            self.session_id, summary=summary, tags=tags
        )

    # ─── البحث الموحد ────────────────────────────────

    async def unified_search(self, query: str, top_k: int = 5,
                             layers: list[str] = None) -> dict:
        """
        بحث موحد عبر كل طبقات الذاكرة.

        Args:
            query: استعلام البحث
            top_k: عدد النتائج لكل طبقة
            layers: طبقات محددة ["hot", "session", "skills", "vector"]

        Returns:
            {
                "results": [...],  # مرتبة بالصلة
                "by_layer": {...}, # نتائج كل طبقة
                "total": int,
                "query": str
            }
        """
        target_layers = layers or ["hot", "session", "skills", "vector"]
        by_layer = {}

        # الطبقة 1: Hot Memory — فحص سريع في snapshot
        if "hot" in target_layers:
            hot_text, user_text = self.hot.load_snapshot()
            hot_results = []
            combined = f"{hot_text}\n{user_text}"
            query_words = query.lower().split()
            for line in combined.split("\n"):
                if any(w in line.lower() for w in query_words):
                    hot_results.append({
                        "layer": "hot",
                        "content": line.strip(),
                        "score": 1.0,  # hot memory دايماً عالية الصلة
                    })
            by_layer["hot"] = hot_results

        # الطبقة 2: Session Search (FTS5) — بحث فوري
        if "session" in target_layers:
            session_results = self.session_search.search(query, limit=top_k)
            by_layer["session"] = [
                {
                    "layer": "session",
                    "content": r.get("content", "")[:500],
                    "score": 0.8,
                    "session_id": r.get("session_id"),
                    "highlight": r.get("highlight", ""),
                    "timestamp": r.get("timestamp"),
                }
                for r in session_results
            ]

        # الطبقة 3: Skills — بحث في المهارات
        if "skills" in target_layers and self.skill_manager:
            skill_results = []
            matched = self.skill_manager.match(query)
            for skill in matched[:top_k]:
                skill_results.append({
                    "layer": "skills",
                    "content": f"[Skill: {skill.name}] {skill.description}",
                    "score": 0.9,
                    "skill_name": skill.name,
                    "instructions": skill.instructions[:300],
                })
            by_layer["skills"] = skill_results

        # الطبقة 4: Vector Memory (Qdrant + SQLite) — بحث دلالي
        if "vector" in target_layers and self.vector:
            try:
                vector_results = await self.vector.retrieve(query, top_k=top_k)
                by_layer["vector"] = [
                    {
                        "layer": "vector",
                        "content": r.get("text", ""),
                        "score": r.get("score", 0),
                        "source": r.get("source", ""),
                        "metadata": r.get("metadata", {}),
                    }
                    for r in vector_results
                ]
            except Exception as e:
                logger.warning(f"خطأ في بحث Qdrant: {e}")
                by_layer["vector"] = []

        # دمج وترتيب كل النتائج
        all_results = []
        for layer, results in by_layer.items():
            all_results.extend(results)

        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return {
            "results": all_results[:top_k * 2],  # ضعف الكمية من كل الطبقات
            "by_layer": by_layer,
            "total": len(all_results),
            "query": query,
        }

    # ─── تخزين موحد ──────────────────────────────────

    async def store_message(self, role: str, content: str, metadata: dict = None):
        """تخزين رسالة في كل الطبقات المناسبة"""
        # Session Search — دائماً
        self.session_search.add_message(
            self.session_id, role, content, metadata
        )

        # Vector Memory — لو متاح
        if self.vector:
            try:
                if role == "user":
                    # تخزين سؤال المستخدم كمحادثة
                    pass  # سيتم عند وجود رد
                elif role == "assistant":
                    # تخزين الرد كمعرفة
                    pass
            except Exception as e:
                logger.warning(f"خطأ في تخزين المتجهات: {e}")

    async def store_conversation(self, question: str, answer: str,
                                 metadata: dict = None):
        """تخزين محادثة كاملة في كل الطبقات"""
        # Vector Memory
        if self.vector:
            try:
                await self.vector.store_conversation(question, answer, metadata)
            except Exception as e:
                logger.warning(f"خطأ في تخزين المحادثة: {e}")

        # Session Search
        self.session_search.add_message(
            self.session_id, "user", question, metadata
        )
        self.session_search.add_message(
            self.session_id, "assistant", answer, metadata
        )

    async def store_knowledge(self, text: str, source: str, topics: list[str] = None):
        """تخزين معرفة جديدة"""
        if self.vector:
            try:
                await self.vector.store_knowledge(text, source, topics)
            except Exception as e:
                logger.warning(f"خطأ في تخزين المعرفة: {e}")

    # ─── إدارة Hot Memory ─────────────────────────────

    def add_memory(self, entry: str, target: str = "memory",
                   origin: str = "agent") -> dict:
        """إضافة مدخل للذاكرة الساخنة"""
        return self.hot.add(entry, target=target, origin=origin)

    def replace_memory(self, old: str, new: str, target: str = "memory",
                       origin: str = "agent") -> dict:
        """استبدال مدخل في الذاكرة الساخنة"""
        return self.hot.replace(old, new, target=target, origin=origin)

    def remove_memory(self, substring: str, target: str = "memory",
                      origin: str = "agent") -> dict:
        """حذف مدخل من الذاكرة الساخنة"""
        return self.hot.remove(substring, target=target, origin=origin)

    def get_hot_for_prompt(self) -> str:
        """محتوى الذاكرة الساخنة جاهز للـ system prompt"""
        return self.hot.get_for_prompt()

    # ─── Memory Nudge ─────────────────────────────────

    def should_nudge(self) -> bool:
        """هل حان وقت تنبيه الذاكرة؟ (كل nudge_interval أدوار)"""
        self._turn_count += 1
        if self._turn_count - self._last_nudge >= self.nudge_interval:
            self._last_nudge = self._turn_count
            return True
        return False

    def get_nudge_prompt(self) -> str:
        """
        تنبيه الذاكرة — يُضاف كرسالة نظام داخلية.
        مثل Hermes — "periodic nudge" للوكيل يراجع نشاطه الأخير.
        """
        stats = self.hot.get_stats()
        memory_pct = stats.get("memory_usage_pct", 0)
        user_pct = stats.get("user_usage_pct", 0)

        nudge = (
            "\n[🧠 تنبيه الذاكرة — راجع نشاطك الأخير]\n"
            "هل تعلمت شيئاً جديداً في الأدوار الأخيرة يستحق التذكر؟\n"
            f"ذاكرتك الشخصية: {stats['memory_chars']}/{stats['memory_limit']} حرف ({memory_pct}%)\n"
            f"ملف المستخدم: {stats['user_chars']}/{stats['user_limit']} حرف ({user_pct}%)\n"
            "إذا تعلمت معرفة جديدة أو لاحظت نمطاً — استخدم أداة memory لإضافته.\n"
            "إذا الذاكرة ممتلئة — وحد المدخلات المتشابهة أولاً."
        )

        if memory_pct > 80:
            nudge += "\n⚠️ ذاكرتك شبه ممتلئة! وحد أو احذف مدخلات قديمة قبل الإضافة."

        return nudge

    # ─── إحصائيات شاملة ──────────────────────────────

    def get_stats(self) -> dict:
        """إحصائيات كل طبقات الذاكرة"""
        stats = {
            "hot_memory": self.hot.get_stats(),
            "session_search": self.session_search.get_stats(),
            "turn_count": self._turn_count,
            "last_nudge_at": self._last_nudge,
            "session_id": self.session_id,
        }

        if self.vector:
            try:
                stats["vector_memory"] = self.vector.get_stats()
            except Exception:
                stats["vector_memory"] = {"error": "unavailable"}

        if self.skill_manager:
            try:
                stats["skills"] = {
                    "total": len(self.skill_manager._skills),
                    "names": list(self.skill_manager._skills.keys()),
                }
            except Exception:
                pass

        return stats
