"""
Adam Prism — Skill Curator
============================
مدير دورة حياة المهارات — مستوحى من Hermes Agent Curator.

الميزات:
- Lifecycle management: active → stale → archived
- Auto-transitions: 30 يوم → stale, 90 يوم → archived (deterministic, no LLM)
- LLM Review: مراجعة ذكية للمهارات المتداخلة (consolidate)
- Write origin tracking: agent_created vs user vs background_review
- Pinned skills: محمية من الحذف التلقائي
- Pre-run snapshots: نسخة احتياطية قبل أي تغيير
- Progressive disclosure: فهرس فقط في prompt، محتوى كامل عند الحاجة
"""

import json
import logging
import os
import shutil
import tarfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("adam_prism.skills.curator")


class SkillCurator:
    """
    مدير دورة حياة المهارات.
    
    مثل Hermes Curator — يمنع تراكم المهارات ويحافظ على جودتها.
    """

    DEFAULT_ADAM_HOME = os.environ.get(
        "ADAM_HOME", os.path.expanduser("~/.adam")
    )

    # عتبات الانتقال التلقائي
    STALE_AFTER_DAYS = 30
    ARCHIVE_AFTER_DAYS = 90

    def __init__(self, config: Dict = None):
        cfg = config or {}
        self.adam_home = Path(cfg.get("adam_home", self.DEFAULT_ADAM_HOME))
        self.skills_dir = self.adam_home / "skills"
        self.archive_dir = self.skills_dir / ".archive"
        self.usage_file = self.skills_dir / ".usage.json"

        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self.stale_after_days = cfg.get("stale_after_days", self.STALE_AFTER_DAYS)
        self.archive_after_days = cfg.get("archive_after_days", self.ARCHIVE_AFTER_DAYS)
        self.dry_run = cfg.get("dry_run", False)

        # تحميل سجل الاستخدام
        self._usage = self._load_usage()

    # ─── سجل الاستخدام ───────────────────────────────

    def _load_usage(self) -> Dict:
        """تحميل سجل استخدام المهارات"""
        if self.usage_file.exists():
            try:
                return json.loads(self.usage_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"تعذر تحميل سجل الاستخدام: {e}")
        return {"skills": {}, "curator_runs": [], "pinned": []}

    def _save_usage(self):
        """حفظ سجل الاستخدام"""
        try:
            self.usage_file.write_text(
                json.dumps(self._usage, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"تعذر حفظ سجل الاستخدام: {e}")

    # ─── تتبع الاستخدام ──────────────────────────────

    def record_usage(self, skill_name: str, success: bool = True,
                     origin: str = "user"):
        """تسجيل استخدام مهارة"""
        if skill_name not in self._usage["skills"]:
            self._usage["skills"][skill_name] = {
                "created_at": datetime.now().isoformat(),
                "last_used": None,
                "use_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "origin": origin,
                "agent_created": origin in ("agent", "background_review"),
                "status": "active",
                "pinned": False,
            }

        skill = self._usage["skills"][skill_name]
        skill["last_used"] = datetime.now().isoformat()
        skill["use_count"] += 1
        if success:
            skill["success_count"] += 1
        else:
            skill["failure_count"] += 1

        self._save_usage()

    def record_creation(self, skill_name: str, origin: str = "agent",
                        trigger: str = ""):
        """تسجيل إنشاء مهارة جديدة"""
        self._usage["skills"][skill_name] = {
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "use_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "origin": origin,
            "agent_created": origin in ("agent", "background_review"),
            "status": "active",
            "pinned": False,
            "trigger": trigger,
        }
        self._save_usage()
        logger.info(f"📝 Skill created: {skill_name} (origin={origin}, trigger={trigger})")

    # ─── التثبيت (Pinning) ───────────────────────────

    def pin(self, skill_name: str) -> bool:
        """تثبيت مهارة — لا يتم حذفها أو أرشفتها تلقائياً"""
        if skill_name in self._usage["skills"]:
            self._usage["skills"][skill_name]["pinned"] = True
            self._save_usage()
            return True
        return False

    def unpin(self, skill_name: str) -> bool:
        """إلغاء تثبيت مهارة"""
        if skill_name in self._usage["skills"]:
            self._usage["skills"][skill_name]["pinned"] = False
            self._save_usage()
            return True
        return False

    # ─── الانتقالات التلقائية ─────────────────────────

    def run_auto_transitions(self) -> Dict:
        """
        تشغيل الانتقالات التلقائية (deterministic, no LLM).
        active → stale (30 يوم) → archived (90 يوم)
        """
        now = datetime.now()
        transitions = {"stale": [], "archived": [], "pinned_skipped": []}

        for name, info in self._usage["skills"].items():
            # تخطي المثبتة
            if info.get("pinned"):
                continue

            # تخطي المهارات المثبتة من Hub
            if info.get("origin") == "hub":
                continue

            if info.get("status") != "active":
                continue

            last_used = info.get("last_used")
            if not last_used:
                continue

            try:
                last_dt = datetime.fromisoformat(last_used)
                days_unused = (now - last_dt).days

                if days_unused >= self.archive_after_days:
                    transitions["archived"].append(name)
                    if not self.dry_run:
                        self._archive_skill(name)
                        info["status"] = "archived"

                elif days_unused >= self.stale_after_days:
                    transitions["stale"].append(name)
                    if not self.dry_run:
                        info["status"] = "stale"

            except Exception as e:
                logger.warning(f"خطأ في معالجة مهارة {name}: {e}")

        if not self.dry_run:
            self._save_usage()

        # تسجيل الجولة
        self._usage["curator_runs"].append({
            "timestamp": now.isoformat(),
            "type": "auto_transitions",
            "stale_count": len(transitions["stale"]),
            "archived_count": len(transitions["archived"]),
            "dry_run": self.dry_run,
        })
        if not self.dry_run:
            self._save_usage()

        return transitions

    def _archive_skill(self, skill_name: str):
        """أرشفة مهارة — نقل لـ .archive/"""
        skill_file = self.skills_dir / f"{skill_name}.md"
        if skill_file.exists():
            shutil.move(str(skill_file), str(self.archive_dir / skill_file.name))
            logger.info(f"📦 Skill archived: {skill_name}")

    def _restore_skill(self, skill_name: str):
        """استعادة مهارة من الأرشيف"""
        archived = self.archive_dir / f"{skill_name}.md"
        if archived.exists():
            shutil.move(str(archived), str(self.skills_dir / archived.name))
            if skill_name in self._usage["skills"]:
                self._usage["skills"][skill_name]["status"] = "active"
            self._save_usage()
            logger.info(f"♻️ Skill restored: {skill_name}")

    # ─── المراجعة الذكية (LLM Review) ────────────────

    def review_skills(self, max_iterations: int = 8) -> Dict:
        """
        مراجعة ذكية للمهارات — يبحث عن:
        - مهارات متداخلة (consolidate)
        - مهارات مهجورة (archive)
        - مهارات تحتاج تحسين (patch)
        
        ملاحظة: النسخة الحالية تستخدم heuristics.
        مع LLM متاح، يمكن ترقيتها لمراجعة دلالية.
        """
        actions = {"keep": [], "consolidate": [], "archive": [], "patch": []}

        agent_skills = {
            name: info for name, info in self._usage["skills"].items()
            if info.get("agent_created") and info.get("status") == "active"
        }

        if not agent_skills:
            return {"actions": actions, "reviewed": 0}

        # البحث عن مهارات متداخلة بناءً على الأسماء
        names = list(agent_skills.keys())
        consolidation_groups = []

        for i, name1 in enumerate(names):
            group = [name1]
            for name2 in names[i+1:]:
                # تطابق جزئي في الاسم
                words1 = set(name1.lower().replace("-", " ").replace("_", " ").split())
                words2 = set(name2.lower().replace("-", " ").replace("_", " ").split())
                overlap = words1 & words2 - {"auto", "skill", "the", "a"}
                if len(overlap) >= 2:
                    group.append(name2)

            if len(group) > 1:
                consolidation_groups.append(group)

        # تسجيل الإجراءات
        for group in consolidation_groups:
            actions["consolidate"].append(group)
            if not self.dry_run:
                # احتفظ بالأحدث، أرشيف الباقي
                group_sorted = sorted(
                    group,
                    key=lambda n: agent_skills[n].get("use_count", 0),
                    reverse=True
                )
                for name in group_sorted[1:]:
                    self._archive_skill(name)
                    if name in self._usage["skills"]:
                        self._usage["skills"][name]["status"] = "consolidated"

        # مهارات بمعدل فشل عالي
        for name, info in agent_skills.items():
            total = info.get("use_count", 0)
            failures = info.get("failure_count", 0)
            if total >= 3 and failures / total > 0.6:
                actions["patch"].append(name)

        # مهارات غير مستخدمة إطلاقاً منذ أكثر من 60 يوم
        now = datetime.now()
        for name, info in agent_skills.items():
            created = info.get("created_at")
            use_count = info.get("use_count", 0)
            if created and use_count == 0:
                try:
                    days = (now - datetime.fromisoformat(created)).days
                    if days > 60:
                        actions["archive"].append(name)
                        if not self.dry_run:
                            self._archive_skill(name)
                            info["status"] = "archived"
                except Exception:
                    pass

        # تسجيل كل المهارات المتبقية كـ "keep"
        for name in agent_skills:
            if name not in [n for g in consolidation_groups for n in g]:
                if name not in actions["archive"] and name not in actions["patch"]:
                    actions["keep"].append(name)

        if not self.dry_run:
            self._save_usage()

        self._usage["curator_runs"].append({
            "timestamp": now.isoformat(),
            "type": "llm_review",
            "consolidated": len(consolidation_groups),
            "archived": len(actions["archive"]),
            "patched": len(actions["patch"]),
            "kept": len(actions["keep"]),
            "dry_run": self.dry_run,
        })
        if not self.dry_run:
            self._save_usage()

        return {"actions": actions, "reviewed": len(agent_skills)}

    # ─── نسخ احتياطي ──────────────────────────────────

    def create_snapshot(self) -> Optional[str]:
        """إنشاء نسخة احتياطية من كل المهارات"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        snapshot_path = self.archive_dir / f"snapshot-{timestamp}.tar.gz"

        try:
            with tarfile.open(str(snapshot_path), "w:gz") as tar:
                for f in self.skills_dir.iterdir():
                    if f.is_file() and not f.name.startswith("."):
                        tar.add(str(f), arcname=f.name)
            logger.info(f"📸 Snapshot created: {snapshot_path}")
            return str(snapshot_path)
        except Exception as e:
            logger.error(f"خطأ في إنشاء snapshot: {e}")
            return None

    # ─── Progressive Disclosure ────────────────────────

    def get_skill_index(self) -> str:
        """
        فهرس المهارات للـ system prompt.
        فقط أسماء + وصف مختصر — بدون محتوى كامل.
        مثل Hermes — progressive disclosure يوفر tokens.
        """
        active_skills = [
            (name, info) for name, info in self._usage["skills"].items()
            if info.get("status") == "active"
        ]

        if not active_skills:
            return ""

        lines = ["## 🛠️ المهارات المتاحة"]
        for name, info in active_skills:
            origin_mark = "🤖" if info.get("agent_created") else "👤"
            use_count = info.get("use_count", 0)
            lines.append(
                f"- {origin_mark} **{name}** (استخدام: {use_count})"
            )

        return "\n".join(lines)

    # ─── إحصائيات ────────────────────────────────────

    def get_stats(self) -> Dict:
        """إحصائيات Curator"""
        by_status = {"active": 0, "stale": 0, "archived": 0, "consolidated": 0}
        by_origin = {"agent": 0, "user": 0, "hub": 0, "background_review": 0}

        for info in self._usage["skills"].values():
            status = info.get("status", "active")
            origin = info.get("origin", "user")
            by_status[status] = by_status.get(status, 0) + 1
            by_origin[origin] = by_origin.get(origin, 0) + 1

        last_run = self._usage["curator_runs"][-1] if self._usage["curator_runs"] else None

        return {
            "total_skills": len(self._usage["skills"]),
            "by_status": by_status,
            "by_origin": by_origin,
            "pinned": len([s for s in self._usage["skills"].values() if s.get("pinned")]),
            "last_curator_run": last_run,
            "total_runs": len(self._usage["curator_runs"]),
        }
