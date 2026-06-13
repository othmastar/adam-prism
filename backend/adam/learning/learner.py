"""
Continuous Learner — بيتعلم من كل محادثة
==========================================
1. Reflection: يراجع الردود ويقيمها
2. Knowledge: يستخرج معلومات جديدة
3. Skills: يكتب مهارات من الحلول الناجحة
4. Reinforcement: يتذكر إيه نجح وإيه تعذر
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("adam_prism.learning")


class ContinuousLearner:
    """التعلم المستمر — يشتغل في الخلفية بعد كل محادثة"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.base_path = Path(self.config.get("learning_path", "./data/learning"))
        self.base_path.mkdir(parents=True, exist_ok=True)

        # سجل التعلم
        self._reflections: list[dict] = []
        self._knowledge: list[dict] = []
        self._generated_skills: list[dict] = []
        self._reinforcement: list[dict] = []

        self._load()

    # ─── الحفظ والتحميل ─────────────────────────────

    def _load(self):
        for name in ("reflections", "knowledge", "generated_skills", "reinforcement"):
            path = self.base_path / f"{name}.json"
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    setattr(self, f"_{name}", data)
                except Exception as e:
                    logger.warning(f"Failed to load {name}: {e}")

    def _save(self, name: str):
        path = self.base_path / f"{name}.json"
        data = getattr(self, f"_{name}", [])[-500:]  # آخر 500 بس
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ─── 1. Reflection ← يراجع الردود ───────────────

    async def reflect(self, message: str, response: str, context: dict) -> dict:
        """يراجع المحادثة ويستخرج تقييم للرد"""
        reflection = {
            "timestamp": datetime.now().isoformat(),
            "message_preview": message[:100],
            "response_preview": response[:100],
            "mode": context.get("mode", "unknown"),
            "cycle": context.get("cycle", 0),
        }

        تقييم = self._auto_evaluate(response, context)
        reflection.update(تقييم)
        self._reflections.append(reflection)
        self._save("reflections")
        return reflection

    def _auto_evaluate(self, response: str, context: dict) -> dict:
        """تقييم تلقائي للرد (بدون نموذج — تحليل نصي)"""
        issues = []
        feedback = "ok"

        # ردود قصيرة جداً
        if len(response) < 5:
            issues.append("short_response")
            feedback = "needs_improvement"

        # ردود طويلة جداً
        elif len(response) > 2000:
            issues.append("verbose")
            feedback = "needs_improvement"

        # كلمات مش هتكون موجودة في رد آدم
        toxic_words = ["أنا مش عارف", "مش متأكد", "sorry", "I don't know"]
        for word in toxic_words:
            if word.lower() in response.lower():
                issues.append("uncertainty")
                feedback = "needs_improvement"
                break

        if not issues:
            feedback = "good"

        return {"feedback": feedback, "issues": issues, "quality_score": len(response) / max(len(response), 1)}

    # ─── 2. Knowledge Extraction ← يستخرج معلومات ───

    async def extract_knowledge(self, message: str, response: str, context: dict) -> dict | None:
        """يستخرج معلومة جديدة من المحادثة (skill-generator placeholder)"""
        # بسيط: أي رد فيه كود أو خطوات → يعتبر معرفة
        if "```" in response or "**" in response:
            knowledge = {
                "timestamp": datetime.now().isoformat(),
                "source_message": message[:200],
                "knowledge_type": "code" if "```" in response else "procedure",
                "preview": response[:300],
                "mode": context.get("mode", "unknown"),
                "applied": False,
            }
            self._knowledge.append(knowledge)
            self._save("knowledge")
            return knowledge
        return None

    # ─── 3. Skill Generation ← يكتب مهارات ───────────

    async def generate_skill(self, knowledge: dict) -> str | None:
        """يولّد skill من معرفة جديدة (placeholder — محتاج LLM)"""
        if knowledge.get("applied"):
            return None

        skill_dir = self.base_path / "generated_skills"
        skill_dir.mkdir(exist_ok=True)

        name = f"auto-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        skill_content = f"""---
{{"name": "{name}", "description": "Auto-generated from conversation", "version": "0.1.0", "author": "adam-learning-system", "triggers": []}}
---

Auto-generated skill based on:
{knowledge.get('source_message', '')[:200]}

Original response:
{knowledge.get('preview', '')[:500]}
"""
        path = skill_dir / f"{name}.md"
        path.write_text(skill_content, encoding="utf-8")

        knowledge["applied"] = True
        record = {"name": name, "path": str(path), "timestamp": datetime.now().isoformat()}
        self._generated_skills.append(record)
        self._save("generated_skills")
        self._save("knowledge")

        logger.info(f"📝 Auto-generated skill: {name}")
        return name

    # ─── 4. Reinforcement ← يتذكر إيه نجح ───────────

    async def record_feedback(self, message: str, response: str, user_rating: str | None = None):
        """يسجل feedback من المستخدم (explicit or implicit)"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "message_preview": message[:100],
            "response_preview": response[:100],
            "rating": user_rating or "unknown",
        }
        self._reinforcement.append(record)
        self._save("reinforcement")

    # ─── Pipeline ← يشغل الكل ──────────────────────

    async def process_interaction(self, message: str, response: str, context: dict) -> dict:
        """معالجة تفاعل كامل: reflection → knowledge → skill generation"""
        result = {"reflection": None, "knowledge": None, "skill": None}

        # 1. Reflection
        result["reflection"] = await self.reflect(message, response, context)

        # 2. Knowledge extraction
        knowledge = await self.extract_knowledge(message, response, context)
        result["knowledge"] = knowledge

        # 3. Skill generation (فقط للردود الجيدة + فيها معرفة)
        if knowledge and result["reflection"].get("feedback") in ("good", "ok"):
            skill_name = await self.generate_skill(knowledge)
            result["skill"] = skill_name

        return result

    # ─── Stats ──────────────────────────────────────

    def get_stats(self) -> dict:
        return {
            "total_reflections": len(self._reflections),
            "total_knowledge": len(self._knowledge),
            "total_generated_skills": len(self._generated_skills),
            "total_feedback": len(self._reinforcement),
            "recent_reflections": self._reflections[-5:],
            "recent_skills": self._generated_skills[-5:],
        }
