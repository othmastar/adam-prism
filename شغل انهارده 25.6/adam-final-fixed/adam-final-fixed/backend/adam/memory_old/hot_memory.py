"""
Adam Prism — Hot Memory (MEMORY.md + USER.md)
==============================================
الطبقة الأولى من الذاكرة: دايماً في system prompt.
مستوحى من Hermes Agent — "Prompt Memory" layer.

الميزات:
- MEMORY.md: ملاحظات الوكيل الشخصية (معرفة، دروس، ملاحظات بيئية)
- USER.md: ملف تعريف المستخدم (تفضيلات، أسلوب، توقعات)
- Frozen Snapshot: تحميل مرة واحدة بالجلسة — لا يتغير أثناء الجلسة
- Capacity Enforcement: حدود أحرف مع توحيد ذكي عند الامتلاء
- Security Scanning: فحص كل entry قبل القبول
- Duplicate Prevention: رفض التكرارات تلقائياً
- Write Approval Gate: اختياري — يحتاج موافقة المستخدم قبل الكتابة
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("adam_prism.memory.hot")

# ═══════════════════════════════════════════════════════
# Security Scanner — فحص أمني لمدخلات الذاكرة
# ═══════════════════════════════════════════════════════

class MemorySecurityScanner:
    """يفحص مدخلات الذاكرة قبل القبول — يمنع حقن الأوامر وتسريب البيانات"""

    # أنماط خطيرة
    INJECTION_PATTERNS = [
        r'ignore\s+.*instructions?',
        r'you\s+are\s+now\s+',
        r'system\s*:\s*',
        r'<\|.*?\|>',
        r'```(python|bash|sh|javascript)',
        r'eval\s*\(',
        r'exec\s*\(',
        r'os\.system\s*\(',
        r'subprocess\.',
        r'import\s+os\b',
        r'__import__\s*\(',
        r'disregard\s+.*(?:above|previous|all)',
        r'forget\s+.*(?:above|previous|all|instructions)',
    ]

    # أنماط بيانات حساسة
    CREDENTIAL_PATTERNS = [
        r'(?:api[_-]?key|secret|password|token|auth)\s*[:=]\s*["\']?\S{8,}',
        r'sk-[a-zA-Z0-9]{20,}',
        r'ghp_[a-zA-Z0-9]{36}',
        r'AKIA[A-Z0-9]{16}',
        r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
    ]

    # أنماط Unicode مخفية
    INVISIBLE_UNICODE = re.compile(
        r'[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff\u00ad]'
    )

    @classmethod
    def scan(cls, entry: str) -> dict:
        """
        فحص أمني شامل لمدخل الذاكرة.
        يرجع: {"safe": bool, "issues": [...], "sanitized": str}
        """
        issues = []

        # 1. فحص حقن الأوامر
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, entry, re.IGNORECASE):
                issues.append(f"injection_pattern: {pattern}")
                break

        # 2. فحص بيانات حساسة
        for pattern in cls.CREDENTIAL_PATTERNS:
            match = re.search(pattern, entry, re.IGNORECASE)
            if match:
                issues.append(f"credential_leak: {pattern[:20]}...")

        # 3. فحص Unicode مخفي
        invisible_matches = cls.INVISIBLE_UNICODE.findall(entry)
        if invisible_matches:
            issues.append(f"invisible_unicode: {len(invisible_matches)} chars found")

        # 4. تنظيف
        sanitized = cls.INVISIBLE_UNICODE.sub('', entry)

        return {
            "safe": len(issues) == 0,
            "issues": issues,
            "sanitized": sanitized,
        }

# ═══════════════════════════════════════════════════════
# Hot Memory — الذاكرة الساخنة
# ═══════════════════════════════════════════════════════

class HotMemory:
    """
    الذاكرة الساخنة — MEMORY.md + USER.md

    دايماً في system prompt. تحميل مرة واحدة بالجلسة (frozen snapshot).
    الكتابة تُحفظ فوراً على القرص لكن لا تظهر في prompt إلا الجلسة القادمة.
    """

    DEFAULT_MEMORY_LIMIT = 2200   # أحرف — مثل Hermes
    DEFAULT_USER_LIMIT = 1375     # أحرف — مثل Hermes
    DEFAULT_ADAM_HOME = os.environ.get(
        "ADAM_HOME", os.path.expanduser("~/.adam")
    )

    def __init__(self, config: dict = None):
        cfg = config or {}
        self.adam_home = Path(cfg.get("adam_home", self.DEFAULT_ADAM_HOME))
        self.memories_dir = self.adam_home / "memories"
        self.memories_dir.mkdir(parents=True, exist_ok=True)

        self.memory_path = self.memories_dir / "MEMORY.md"
        self.user_path = self.memories_dir / "USER.md"

        self.memory_char_limit = cfg.get("memory_char_limit", self.DEFAULT_MEMORY_LIMIT)
        self.user_char_limit = cfg.get("user_char_limit", self.DEFAULT_USER_LIMIT)
        self.write_approval = cfg.get("write_approval", False)  # يحتاج موافقة المستخدم

        # Frozen snapshot — يُحمّل مرة واحدة بالجلسة
        self._memory_snapshot: str | None = None
        self._user_snapshot: str | None = None
        self._snapshot_loaded = False

        # مراجع الانتظار (pending writes — تنتظر موافقة المستخدم)
        self._pending_writes: list[dict] = []

    # ─── تحميل الـ Snapshot ──────────────────────────

    def load_snapshot(self) -> tuple[str, str]:
        """
        تحميل snapshot مرة واحدة بالجلسة.
        الـ snapshot لا يتغير أثناء الجلسة — يحافظ على cache.
        """
        if not self._snapshot_loaded:
            self._memory_snapshot = self._read_file(self.memory_path)
            self._user_snapshot = self._read_file(self.user_path)
            self._snapshot_loaded = True
            logger.info(
                f"Hot Memory snapshot loaded: "
                f"MEMORY={len(self._memory_snapshot)} chars, "
                f"USER={len(self._user_snapshot)} chars"
            )
        return self._memory_snapshot or "", self._user_snapshot or ""

    def refresh_snapshot(self):
        """إعادة تحميل الـ snapshot — تُستخدم في بداية جلسة جديدة"""
        self._snapshot_loaded = False
        return self.load_snapshot()

    def get_for_prompt(self) -> str:
        """يرجع محتوى الذاكرة الساخنة جاهز لوضعه في system prompt"""
        memory_text, user_text = self.load_snapshot()
        parts = []

        if memory_text.strip():
            parts.append(f"## 🧠 ذاكرتي الشخصية (MEMORY)\n{memory_text}")
        if user_text.strip():
            parts.append(f"## 👤 ملف تعريف المستخدم (USER)\n{user_text}")

        return "\n\n".join(parts) if parts else ""

    # ─── قراءة/كتابة الملفات ─────────────────────────

    def _read_file(self, path: Path) -> str:
        """قراءة ملف ذاكرة"""
        try:
            if path.exists():
                return path.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.warning(f"تعذر قراءة {path}: {e}")
        return ""

    def _write_file(self, path: Path, content: str) -> bool:
        """كتابة ملف ذاكرة"""
        try:
            path.write_text(content.strip() + "\n", encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"تعذر كتابة {path}: {e}")
            return False

    # ─── إدارة المدخلات ──────────────────────────────

    def _parse_entries(self, text: str) -> list[str]:
        """تحليل النص لمدخلات فردية (كل سطر يبدأ بـ - هو مدخل)"""
        if not text.strip():
            return []
        entries = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                entries.append(line)
            elif line and not line.startswith("#") and entries:
                # سطر مكمل للمدخل السابق
                entries[-1] += " " + line
        return entries

    def _entries_to_text(self, entries: list[str]) -> str:
        """تحويل المدخلات لنص"""
        return "\n".join(entries)

    def _current_char_count(self, target: str = "memory") -> int:
        """عدد الأحرف الحالية"""
        if target == "memory":
            return len(self._read_file(self.memory_path))
        return len(self._read_file(self.user_path))

    # ─── العمليات العامة ──────────────────────────────

    def add(self, entry: str, target: str = "memory",
            origin: str = "user", require_approval: bool = None) -> dict:
        """
        إضافة مدخل جديد.

        Args:
            entry: النص المراد إضافته
            target: "memory" أو "user"
            origin: "user" | "agent" | "background_review" | "nudge"
            require_approval: فرض طلب موافقة المستخدم

        Returns:
            {"success": bool, "reason": str, "needs_approval": bool}
        """
        entry = entry.strip()
        if not entry:
            return {"success": False, "reason": "مدخل فارغ", "needs_approval": False}

        # فحص أمني
        scan = MemorySecurityScanner.scan(entry)
        if not scan["safe"]:
            logger.warning(f"مدخل ذاكرة مرفوض أمنياً: {scan['issues']}")
            return {
                "success": False,
                "reason": f"محتوى غير آمن: {', '.join(scan['issues'][:2])}",
                "needs_approval": False,
            }
        entry = scan["sanitized"]

        # تنسيق المدخل
        if not entry.startswith("- "):
            entry = f"- {entry}"

        # فحص التكرار
        path = self.memory_path if target == "memory" else self.user_path
        current = self._read_file(path)
        entries = self._parse_entries(current)

        for existing in entries:
            if existing.strip().lower() == entry.strip().lower():
                return {"success": False, "reason": "مدخل مكرر", "needs_approval": False}

        # فحص السعة
        limit = self.memory_char_limit if target == "memory" else self.user_char_limit
        new_content = current + "\n" + entry if current else entry

        if len(new_content) > limit:
            return {
                "success": False,
                "reason": f"تجاوز الحد ({len(new_content)}/{limit} حرف). وحد أو احذف مدخلات أولاً.",
                "needs_approval": False,
                "current_entries": entries,
                "limit": limit,
                "current_chars": len(current),
            }

        # فحص الموافقة
        needs_approval = require_approval if require_approval is not None else self.write_approval
        if needs_approval:
            self._pending_writes.append({
                "action": "add", "entry": entry, "target": target,
                "origin": origin, "timestamp": datetime.now().isoformat(),
            })
            return {"success": False, "reason": "في انتظار موافقة المستخدم", "needs_approval": True}

        # كتابة فورية
        success = self._write_file(path, new_content)
        if success:
            logger.info(f"📝 Hot Memory add [{target}]: {entry[:60]}...")
        return {"success": success, "reason": "تمت الإضافة", "needs_approval": False}

    def replace(self, old_substring: str, new_entry: str, target: str = "memory",
                origin: str = "user", require_approval: bool = None) -> dict:
        """
        استبدال مدخل بناءً على مطابقة جزئية (substring matching).
        مثل Hermes — لا يحتاج النص الكامل.
        """
        path = self.memory_path if target == "memory" else self.user_path
        current = self._read_file(path)
        entries = self._parse_entries(current)

        # تنسيق المدخل الجديد
        if not new_entry.startswith("- "):
            new_entry = f"- {new_entry}"

        # فحص أمني
        scan = MemorySecurityScanner.scan(new_entry)
        if not scan["safe"]:
            return {"success": False, "reason": f"محتوى غير آمن: {scan['issues']}"}
        new_entry = scan["sanitized"]

        # البحث عن المدخل المطابق
        found = False
        new_entries = []
        for e in entries:
            if old_substring.lower() in e.lower() and not found:
                new_entries.append(new_entry)
                found = True
            else:
                new_entries.append(e)

        if not found:
            return {"success": False, "reason": f"لم يتم العثور على مدخل يحتوي: {old_substring[:50]}"}

        new_content = self._entries_to_text(new_entries)
        limit = self.memory_char_limit if target == "memory" else self.user_char_limit

        if len(new_content) > limit:
            return {
                "success": False,
                "reason": f"تجاوز الحد بعد الاستبدال ({len(new_content)}/{limit})",
                "needs_approval": False,
            }

        # فحص الموافقة
        needs_approval = require_approval if require_approval is not None else self.write_approval
        if needs_approval:
            self._pending_writes.append({
                "action": "replace", "old": old_substring, "new": new_entry,
                "target": target, "origin": origin,
            })
            return {"success": False, "reason": "في انتظار موافقة المستخدم", "needs_approval": True}

        success = self._write_file(path, new_content)
        if success:
            logger.info(f"📝 Hot Memory replace [{target}]: {old_substring[:30]} → {new_entry[:30]}")
        return {"success": success, "reason": "تم الاستبدال", "needs_approval": False}

    def remove(self, substring: str, target: str = "memory",
               origin: str = "user", require_approval: bool = None) -> dict:
        """حذف مدخل بناءً على مطابقة جزئية"""
        path = self.memory_path if target == "memory" else self.user_path
        current = self._read_file(path)
        entries = self._parse_entries(current)

        new_entries = []
        removed = []
        for e in entries:
            if substring.lower() in e.lower() and not removed:
                removed.append(e)
            else:
                new_entries.append(e)

        if not removed:
            return {"success": False, "reason": f"لم يتم العثور على: {substring[:50]}"}

        new_content = self._entries_to_text(new_entries)

        # فحص الموافقة
        needs_approval = require_approval if require_approval is not None else self.write_approval
        if needs_approval:
            self._pending_writes.append({
                "action": "remove", "substring": substring,
                "target": target, "origin": origin,
            })
            return {"success": False, "reason": "في انتظار موافقة المستخدم", "needs_approval": True}

        success = self._write_file(path, new_content)
        if success:
            logger.info(f"🗑️ Hot Memory remove [{target}]: {removed[0][:50]}")
        return {"success": success, "reason": "تم الحذف", "needs_approval": False}

    def consolidate(self, target: str = "memory") -> dict:
        """
        توحيد المدخلات — يدمج المتشابهات ويحذف المكررات.
        يُستدعى عندما تكون الذاكرة ممتلئة.
        """
        path = self.memory_path if target == "memory" else self.user_path
        current = self._read_file(path)
        entries = self._parse_entries(current)

        if not entries:
            return {"success": False, "reason": "لا توجد مدخلات للتوحيد"}

        # إزالة التكرارات
        seen = set()
        unique = []
        for e in entries:
            key = e.strip().lower()
            if key not in seen:
                seen.add(key)
                unique.append(e)

        # محاولة دمج مدخلات قصيرة مرتبطة
        merged = []
        skip = set()
        for i, e1 in enumerate(unique):
            if i in skip:
                continue
            for j, e2 in enumerate(unique[i+1:], start=i+1):
                if j in skip:
                    continue
                # لو مدخلين قصيرين عن نفس الموضوع — ادمجهم
                if len(e1) < 80 and len(e2) < 80:
                    words1 = set(e1.lower().split())
                    words2 = set(e2.lower().split())
                    overlap = words1 & words2 - {"-", "و", "في", "من", "على", "إلى", "the", "a", "an", "is", "are"}
                    if len(overlap) >= 2:
                        merged_entry = f"- {e1[2:].strip()} | {e2[2:].strip()}"
                        merged.append(merged_entry)
                        skip.add(i)
                        skip.add(j)
                        break
            if i not in skip:
                merged.append(e1)

        new_content = self._entries_to_text(merged)
        success = self._write_file(path, new_content)

        return {
            "success": success,
            "reason": f"تم التوحيد: {len(entries)} → {len(merged)} مدخل",
            "original_count": len(entries),
            "new_count": len(merged),
            "saved_chars": len(current) - len(new_content),
        }

    # ─── إدارة الموافقات ─────────────────────────────

    def get_pending_writes(self) -> list[dict]:
        """استرجاع الكتابات المعلقة"""
        return list(self._pending_writes)

    def approve_write(self, index: int) -> dict:
        """الموافقة على كتابة معلقة"""
        if index < 0 or index >= len(self._pending_writes):
            return {"success": False, "reason": "فهرس غير صالح"}

        pending = self._pending_writes.pop(index)
        action = pending["action"]

        if action == "add":
            return self.add(pending["entry"], pending["target"], pending["origin"], require_approval=False)
        elif action == "replace":
            return self.replace(pending["old"], pending["new"], pending["target"], pending["origin"], require_approval=False)
        elif action == "remove":
            return self.remove(pending["substring"], pending["target"], pending["origin"], require_approval=False)

        return {"success": False, "reason": f"إجراء غير معروف: {action}"}

    def reject_write(self, index: int) -> dict:
        """رفض كتابة معلقة"""
        if index < 0 or index >= len(self._pending_writes):
            return {"success": False, "reason": "فهرس غير صالح"}
        self._pending_writes.pop(index)
        return {"success": True, "reason": "تم الرفض"}

    # ─── إحصائيات ────────────────────────────────────

    def get_stats(self) -> dict:
        """إحصائيات الذاكرة الساخنة"""
        memory_text = self._read_file(self.memory_path)
        user_text = self._read_file(self.user_path)
        memory_entries = self._parse_entries(memory_text)
        user_entries = self._parse_entries(user_text)

        return {
            "memory_chars": len(memory_text),
            "memory_limit": self.memory_char_limit,
            "memory_usage_pct": round(len(memory_text) / self.memory_char_limit * 100, 1) if self.memory_char_limit else 0,
            "memory_entries": len(memory_entries),
            "user_chars": len(user_text),
            "user_limit": self.user_char_limit,
            "user_usage_pct": round(len(user_text) / self.user_char_limit * 100, 1) if self.user_char_limit else 0,
            "user_entries": len(user_entries),
            "pending_writes": len(self._pending_writes),
            "snapshot_loaded": self._snapshot_loaded,
        }
