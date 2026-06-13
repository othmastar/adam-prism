"""
Adam Prism — Closed Learning Loop
====================================
حلقة التعلم المغلقة — مستوحى من Hermes Agent.

المفهوم: Memory → Skills → Session Search → Memory
حلقة مستمرة تتعلم من كل تفاعل وتحسّن نفسها.

المكونات:
1. MemoryNudge: تنبيه دوري للوكيل يراجع نشاطه ويكتب للذاكرة
2. SkillCreator: إنشاء مهارات تلقائي بمحفزات محددة
3. SkillImprover: تحسين المهارات أثناء الاستخدام (patch/edit)
4. ClosedLoop: الحلقة الكاملة — ينسق بين كل المكونات

المحفزات (Triggers) لإنشاء مهارة:
- مهمة مع 5+ استدعاءات أدوات ناجحة → complex_workflow
- تعافي من أخطاء → error_recovery
- تصحيح المستخدم للمنهج → user_correction
- سير عمل جديد/غير معتاد → novel_workflow
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger("adam_prism.learning.closed_loop")


# ═══════════════════════════════════════════════════════
# Memory Nudge — تنبيه الذاكرة الدوري
# ═══════════════════════════════════════════════════════

class MemoryNudge:
    """
    تنبيه دوري للوكيل — يطلب منه مراجعة نشاطه الأخير
    وكتابة أي شيء يستحق التذكر للذاكرة.
    
    مثل Hermes — كل ~10 أدوار، الوكيل يستلم nudge.
    """

    def __init__(self, unified_memory=None, interval: int = 10):
        self.unified_memory = unified_memory
        self.interval = interval
        self._turn_count = 0
        self._nudges_given = 0

    def process_turn(self) -> Optional[str]:
        """
        معالجة دور — يرجع nudge prompt لو حان الوقت.
        يرجع None لو لسه بدري.
        """
        self._turn_count += 1
        if self._turn_count % self.interval == 0 and self._turn_count > 0:
            self._nudges_given += 1
            return self._build_nudge()
        return None

    def _build_nudge(self) -> str:
        """بناء رسالة التنبيه"""
        stats = {}
        if self.unified_memory:
            stats = self.unified_memory.get_stats()

        hot_stats = stats.get("hot_memory", {})
        memory_pct = hot_stats.get("memory_usage_pct", 0)
        user_pct = hot_stats.get("user_usage_pct", 0)

        nudge = (
            "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🧠 [تنبيه الذاكرة الدوري — دور {turn}]\n"
            "راجع نشاطك الأخير:\n"
            "- هل تعلمت معرفة جديدة؟ → أضفها لذاكرتك (memory add)\n"
            "- هل لاحظت نمطاً في تفضيلات المستخدم؟ → حدّث ملفه (memory add --target user)\n"
            "- هل اكتشفت إجراءً يُعاد؟ → أنشئ مهارة (skill create)\n"
            f"- ذاكرتك: {hot_stats.get('memory_chars', 0)}/{hot_stats.get('memory_limit', 2200)} حرف ({memory_pct}%)\n"
            f"- ملف المستخدم: {hot_stats.get('user_chars', 0)}/{hot_stats.get('user_limit', 1375)} حرف ({user_pct}%)\n"
        )

        if memory_pct > 80:
            nudge += "\n⚠️ ذاكرتك شبه ممتلئة! وحد المدخلات أولاً (memory consolidate)."

        nudge += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return nudge.format(turn=self._turn_count)

    def get_stats(self) -> Dict:
        return {
            "turn_count": self._turn_count,
            "nudges_given": self._nudges_given,
            "interval": self.interval,
        }


# ═══════════════════════════════════════════════════════
# Skill Creator — إنشاء مهارات تلقائي
# ═══════════════════════════════════════════════════════

class SkillCreator:
    """
    إنشاء مهارات تلقائي بناءً على محفزات محددة.
    
    مثل Hermes — الوكيل ينشئ skills تلقائياً عندما:
    1. مهمة معقدة (5+ أدوات)
    2. تعافي من خطأ
    3. تصحيح من المستخدم
    4. سير عمل جديد
    """

    SKILL_TRIGGERS = {
        "complex_workflow": {
            "condition": "tool_calls >= 5 and all successful",
            "description": "سير عمل معقد يستحق التوثيق",
        },
        "error_recovery": {
            "condition": "tool failed then succeeded with different approach",
            "description": "مسار التعافي من خطأ",
        },
        "user_correction": {
            "condition": "user corrected the agent's approach",
            "description": "التصحيح يجب أن يُتذكر",
        },
        "novel_workflow": {
            "condition": "unusual tool combination or approach",
            "description": "إجراء جديد يستحق التوثيق",
        },
    }

    def __init__(self, skill_manager=None, curator=None, config: Dict = None):
        self.skill_manager = skill_manager
        self.curator = curator
        self.config = config or {}
        self._created_skills: List[Dict] = []

    def evaluate_triggers(self, context: Dict) -> List[str]:
        """
        تقييم المحفزات بناءً على سياق التفاعل.
        يرجع قائمة بالمحفزات المنشطة.
        """
        triggered = []

        tool_records = context.get("tool_records", [])
        tool_calls = len(tool_records)
        all_success = all(t.get("success", False) for t in tool_records) if tool_records else False

        # complex_workflow: 5+ أدوات ناجحة
        if tool_calls >= 5 and all_success:
            triggered.append("complex_workflow")

        # error_recovery: فشل ثم نجاح
        if tool_records:
            has_failure = any(not t.get("success", False) for t in tool_records)
            has_success_after = False
            failed = False
            for t in tool_records:
                if not t.get("success", False):
                    failed = True
                elif failed and t.get("success", False):
                    has_success_after = True
            if has_failure and has_success_after:
                triggered.append("error_recovery")

        # novel_workflow: تركيبة أدوات غير عادية
        if tool_calls >= 3:
            tool_names = [t.get("name", "") for t in tool_records]
            unique_tools = len(set(tool_names))
            if unique_tools >= 3:
                triggered.append("novel_workflow")

        # user_correction: إشارة من سياق المحادثة
        if context.get("user_correction"):
            triggered.append("user_correction")

        return triggered

    def should_create_skill(self, context: Dict) -> Optional[str]:
        """
        هل يجب إنشاء مهارة؟ يرجع نوع المحفز أو None.
        """
        triggers = self.evaluate_triggers(context)
        if triggers:
            # أولوية: user_correction > error_recovery > complex_workflow > novel_workflow
            priority = ["user_correction", "error_recovery", "complex_workflow", "novel_workflow"]
            for p in priority:
                if p in triggers:
                    return p
        return None

    async def create_skill_from_context(self, context: Dict,
                                         trigger: str = None) -> Optional[str]:
        """
        إنشاء مهارة من سياق التفاعل.
        يرجع اسم المهارة أو None.
        """
        if not trigger:
            trigger = self.should_create_skill(context)
        if not trigger:
            return None

        # بناء محتوى المهارة
        name = f"auto-{trigger}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        tool_records = context.get("tool_records", [])
        tool_sequence = " → ".join([t.get("name", "?") for t in tool_records])

        # وصف المحفز
        trigger_info = self.SKILL_TRIGGERS.get(trigger, {})
        description = trigger_info.get("description", trigger)

        # محتوى المهارة
        skill_content = f"""---
{{"name": "{name}", "description": "{description}", "version": "0.1.0", "author": "adam-closed-loop", "triggers": [], "origin": "agent"}}
---

# {description}

## متى تستخدم
عندما تواجه مهمة مشابهة لـ: {context.get('message_preview', '')[:100]}

## الإجراء
1. {chr(10).join(f'{i+1}. استخدم {t.get("name", "?")} → {"نجاح" if t.get("success") else "فشل"}' for i, t in enumerate(tool_records[:8]))}

## تسلسل الأدوات
{tool_sequence}

## ملاحظات
- تم إنشاؤها تلقائياً بواسطة Closed Learning Loop
- المحفز: {trigger}
- تاريخ الإنشاء: {datetime.now().isoformat()}
"""

        # حفظ المهارة
        if self.skill_manager:
            try:
                skill_dir = Path.home() / ".adam" / "skills"
                skill_dir.mkdir(parents=True, exist_ok=True)
                skill_path = skill_dir / f"{name}.md"
                skill_path.write_text(skill_content, encoding="utf-8")

                # تسجيل في Curator
                if self.curator:
                    self.curator.record_creation(name, origin="agent", trigger=trigger)

                logger.info(f"📝 Auto-created skill: {name} (trigger={trigger})")
                self._created_skills.append({
                    "name": name,
                    "trigger": trigger,
                    "timestamp": datetime.now().isoformat(),
                })
                return name
            except Exception as e:
                logger.error(f"خطأ في إنشاء المهارة: {e}")

        return None

    def get_stats(self) -> Dict:
        return {
            "total_created": len(self._created_skills),
            "recent_creates": self._created_skills[-5:],
        }


# ═══════════════════════════════════════════════════════
# Skill Improver — تحسين المهارات أثناء الاستخدام
# ═══════════════════════════════════════════════════════

class SkillImprover:
    """
    تحسين المهارات أثناء الاستخدام.
    
    مثل Hermes:
    - patch: إصلاح موجه (مفضل — لا يكسر ما يعمل)
    - edit: إعادة كتابة كاملة (للتغييرات الكبيرة)
    """

    def __init__(self, skill_manager=None, curator=None):
        self.skill_manager = skill_manager
        self.curator = curator
        self._patches: List[Dict] = []

    async def patch_skill(self, skill_name: str, old_text: str,
                          new_text: str) -> Dict:
        """
        إصلاح موجه لمهارة — يغير جزء محدد فقط.
        مفضل على edit لأنه لا يكسر ما يعمل.
        """
        if not self.skill_manager:
            return {"success": False, "reason": "لا يوجد مدير مهارات"}

        skill = self.skill_manager.get(skill_name)
        if not skill:
            return {"success": False, "reason": f"مهارة غير موجودة: {skill_name}"}

        if old_text not in skill.instructions:
            return {"success": False, "reason": "النص القديم غير موجود في المهارة"}

        # تطبيق الـ patch
        new_instructions = skill.instructions.replace(old_text, new_text, 1)
        skill.instructions = new_instructions

        # حفظ على القرص
        try:
            skill_path = Path.home() / ".adam" / "skills" / f"{skill_name}.md"
            if skill_path.exists():
                content = skill_path.read_text(encoding="utf-8")
                updated = content.replace(old_text, new_text, 1)
                skill_path.write_text(updated, encoding="utf-8")
        except Exception as e:
            logger.error(f"خطأ في حفظ patch: {e}")
            return {"success": False, "reason": str(e)}

        # تسجيل الاستخدام في Curator
        if self.curator:
            self.curator.record_usage(skill_name, success=True, origin="patch")

        self._patches.append({
            "skill": skill_name,
            "old": old_text[:50],
            "new": new_text[:50],
            "timestamp": datetime.now().isoformat(),
        })

        logger.info(f"🔧 Skill patched: {skill_name}")
        return {"success": True, "reason": "تم الإصلاح"}

    async def edit_skill(self, skill_name: str,
                         new_content: str) -> Dict:
        """
        إعادة كتابة كاملة لمهارة.
        تستخدم فقط للتغييرات الكبيرة.
        """
        if not self.skill_manager:
            return {"success": False, "reason": "لا يوجد مدير مهارات"}

        skill = self.skill_manager.get(skill_name)
        if not skill:
            return {"success": False, "reason": f"مهارة غير موجودة: {skill_name}"}

        # تحديث المحتوى
        skill.instructions = new_content

        # حفظ على القرص
        try:
            skill_path = Path.home() / ".adam" / "skills" / f"{skill_name}.md"
            if skill_path.exists():
                # الحفاظ على الـ frontmatter
                content = skill_path.read_text(encoding="utf-8")
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        updated = f"---{parts[1]}---\n\n{new_content}"
                    else:
                        updated = new_content
                else:
                    updated = new_content
                skill_path.write_text(updated, encoding="utf-8")
        except Exception as e:
            logger.error(f"خطأ في حفظ edit: {e}")
            return {"success": False, "reason": str(e)}

        logger.info(f"✏️ Skill edited: {skill_name}")
        return {"success": True, "reason": "تم التعديل"}

    def get_stats(self) -> Dict:
        return {
            "total_patches": len(self._patches),
            "recent_patches": self._patches[-5:],
        }


# ═══════════════════════════════════════════════════════
# Closed Learning Loop — الحلقة الكاملة
# ═══════════════════════════════════════════════════════

class ClosedLearningLoop:
    """
    حلقة التعلم المغلقة — Memory → Skills → Search → Memory
    
    تنسق بين كل مكونات التعلم:
    1. MemoryNudge: تنبيه دوري للذاكرة
    2. SkillCreator: إنشاء مهارات تلقائي
    3. SkillImprover: تحسين المهارات
    4. Curator: إدارة دورة حياة المهارات
    5. UnifiedMemory: البحث والتخزين الموحد
    
    يتم تشغيلها كـ background task بعد كل تفاعل.
    """

    def __init__(self, unified_memory=None, skill_manager=None,
                 curator=None, config: Dict = None):
        self.config = config or {}
        self.unified_memory = unified_memory
        self.skill_manager = skill_manager
        self.curator = curator

        # المكونات
        self.nudge = MemoryNudge(
            unified_memory=unified_memory,
            interval=self.config.get("nudge_interval", 10)
        )
        self.creator = SkillCreator(
            skill_manager=skill_manager,
            curator=curator,
            config=self.config
        )
        self.improver = SkillImprover(
            skill_manager=skill_manager,
            curator=curator
        )

        # إحصائيات الحلقة
        self._loop_count = 0
        self._skills_created = 0
        self._nudges_given = 0

    async def process_interaction(self, user_message: str, response: str,
                                   context: Dict) -> Dict:
        """
        معالجة تفاعل في الحلقة المغلقة.
        يُشغَّل كـ background task بعد كل chat cycle.
        
        الحلقة:
        1. فحص nudge → إرسال تنبيه للذاكرة
        2. تقييم triggers → إنشاء مهارة إذا لزم
        3. تخزين في الذاكرة الموحدة
        4. تسجيل الاستخدام في Curator
        """
        self._loop_count += 1
        result = {
            "loop_count": self._loop_count,
            "nudge": None,
            "skill_created": None,
            "stored": False,
        }

        # 1. Memory Nudge — هل حان وقت التنبيه؟
        nudge_prompt = self.nudge.process_turn()
        if nudge_prompt:
            result["nudge"] = nudge_prompt
            self._nudges_given += 1

        # 2. Skill Creation — هل يجب إنشاء مهارة؟
        context["message_preview"] = user_message[:100]
        trigger = self.creator.should_create_skill(context)
        if trigger:
            skill_name = await self.creator.create_skill_from_context(context, trigger)
            if skill_name:
                result["skill_created"] = skill_name
                self._skills_created += 1

        # 3. تخزين في الذاكرة الموحدة
        if self.unified_memory:
            try:
                await self.unified_memory.store_conversation(
                    question=user_message,
                    answer=response,
                    metadata={"mode": context.get("mode", "unknown"), "loop": self._loop_count}
                )
                result["stored"] = True
            except Exception as e:
                logger.warning(f"خطأ في تخزين الحلقة: {e}")

        # 4. تسجيل استخدام المهارات المنفذة
        if self.curator:
            for tool in context.get("tool_records", []):
                self.curator.record_usage(
                    tool.get("name", "unknown"),
                    success=tool.get("success", False),
                    origin="agent"
                )

        return result

    def get_nudge_if_needed(self) -> Optional[str]:
        """الحصول على nudge prompt لو حان الوقت (للدمج في system prompt)"""
        return self.nudge.process_turn()

    def get_stats(self) -> Dict:
        """إحصائيات الحلقة المغلقة"""
        return {
            "loop_count": self._loop_count,
            "skills_created": self._skills_created,
            "nudges_given": self._nudges_given,
            "nudge_stats": self.nudge.get_stats(),
            "creator_stats": self.creator.get_stats(),
            "improver_stats": self.improver.get_stats(),
        }
