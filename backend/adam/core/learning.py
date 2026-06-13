"""
Adam Prism — PreferenceLearner (Phase 2: Self-Learning)
========================================================
يتعلم من قرارات المستخدم: إيه اللي بيسمح بيه وإيه اللي بيرفضه.
بيخزن التفضيلات في ملف JSON ويستخدمها للتنبؤ بالسلوك المستقبلي.

No weights, no fine-tuning — كل حاجة state-based.
"""

import json
import logging
import os
from datetime import datetime

logger = logging.getLogger("adam_prism.learning")

NOTES_DIR = os.environ.get("ADAM_NOTEBOOK_DIR", os.path.expanduser("~/.local/adam_notebook"))
PREFERENCES_PATH = os.path.join(NOTES_DIR, "preferences.json")
HISTORY_PATH = os.path.join(NOTES_DIR, "decision_history.json")


class PreferenceLearner:
    """يتعلم تفضيلات المستخدم من قرارات الصلاحية"""

    def __init__(self):
        self.preferences: dict[str, dict] = self._load_preferences()
        self.history: list[dict] = self._load_history()
        self._session_decisions: list[dict] = []

    # ─── التخزين ─────────────────────────────────

    def _load_preferences(self) -> dict:
        try:
            if os.path.exists(PREFERENCES_PATH):
                with open(PREFERENCES_PATH, encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            logger.exception("تعذر تحميل التفضيلات:")
        return {}

    def _save_preferences(self):
        try:
            os.makedirs(NOTES_DIR, exist_ok=True)
            with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception("تعذر حفظ التفضيلات:")

    def _load_history(self) -> list:
        try:
            if os.path.exists(HISTORY_PATH):
                with open(HISTORY_PATH, encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_history(self):
        try:
            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(self.history[-500:], f, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception("تعذر حفظ التاريخ:")

    # ─── التسجيل ─────────────────────────────────

    def record_decision(self, tool: str, category: str, verdict: str, reason: str = ""):
        """تسجيل قرار المستخدم (granted/denied)"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool,
            "category": category,
            "verdict": verdict,
            "reason": reason,
        }
        self.history.append(entry)
        self._session_decisions.append(entry)
        self._save_history()

        # تحديث الإحصائيات لكل فئة
        if category not in self.preferences:
            self.preferences[category] = {"allow": 0, "deny": 0, "last": None, "tools": {}}

        cat = self.preferences[category]
        if verdict == "granted":
            cat["allow"] += 1
        elif verdict == "denied":
            cat["deny"] += 1
        cat["last"] = verdict

        if tool not in cat["tools"]:
            cat["tools"][tool] = {"allow": 0, "deny": 0}
        if verdict == "granted":
            cat["tools"][tool]["allow"] += 1
        elif verdict == "denied":
            cat["tools"][tool]["deny"] += 1

        self._save_preferences()

    # ─── التنبؤ ───────────────────────────────────

    def predict(self, tool: str, category: str) -> str:
        """
        يتنبأ بقرار المستخدم بناءً على التاريخ.
        Returns: "likely_allow" | "likely_deny" | "unknown"
        """
        cat = self.preferences.get(category)
        if not cat:
            return "unknown"

        total = cat["allow"] + cat["deny"]
        if total < 3:
            return "unknown"  # مش كفاية بيانات

        # الأولوية: قرارات الأداة المحددة
        tool_stats = cat["tools"].get(tool)
        if tool_stats:
            t_total = tool_stats["allow"] + tool_stats["deny"]
            if t_total >= 2:
                if tool_stats["allow"] > tool_stats["deny"]:
                    return "likely_allow"
                elif tool_stats["deny"] > tool_stats["allow"]:
                    return "likely_deny"

        # لو مفيش بيانات كفاية على الأداة — استخدم إحصائيات الفئة
        allow_ratio = cat["allow"] / total if total > 0 else 0.5
        if allow_ratio >= 0.7:
            return "likely_allow"
        elif allow_ratio <= 0.3:
            return "likely_deny"
        return "unknown"

    # ─── الاستعلام ─────────────────────────────────

    def get_summary(self) -> dict:
        """ملخص التفضيلات المتعلمة"""
        summary = {}
        for cat, stats in self.preferences.items():
            total = stats["allow"] + stats["deny"]
            if total > 0:
                summary[cat] = {
                    "total_decisions": total,
                    "allow_rate": round(stats["allow"] / total * 100, 1),
                    "last_decision": stats["last"],
                    "tools": list(stats.get("tools", {}).keys()),
                }
        return summary

    def get_session_decisions(self) -> list[dict]:
        """قرارات الجلسة الحالية"""
        return self._session_decisions

    def clear_session(self):
        """مسح ذاكرة الجلسة"""
        self._session_decisions = []

    def likely_allow(self, tool: str, category: str) -> bool:
        return self.predict(tool, category) == "likely_allow"

    def likely_deny(self, tool: str, category: str) -> bool:
        return self.predict(tool, category) == "likely_deny"
