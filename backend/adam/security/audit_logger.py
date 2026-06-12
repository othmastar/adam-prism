"""
Adam Prism — Tamper-Proof Audit Logger
========================================
سجل تدقيق مقاوم للتلاعب مع سلسلة تجزئة SHA-256.

A tamper-proof audit logging system that chains entries using SHA-256 hashes.
Each log entry includes the hash of the previous entry, making it possible to
detect any tampering or deletion of records.

المميزات / Features:
  - سلسلة تجزئة SHA-256 — Hash chain for tamper detection
  - تنسيق JSON Lines (كائن JSON لكل سطر) — JSON Lines format
  - تدوير تلقائي يومي — Daily auto-rotation
  - التحقق من السلامة — Integrity verification
  - بحث في السجلات — Log search
  - عمليات آمنة وغير متزامنة — Async and thread-safe operations
  - دوال مساعدة مخصصة — Helper functions for common audit events
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("adam_prism.security.audit")


# ═══════════════════════════════════════════════════════════════
# Audit Logger
# ═══════════════════════════════════════════════════════════════

class AuditLogger:
    """
    سجل تدقيق مقاوم للتلاعم — Tamper-proof audit logger.

    كل سجل يتضمن تجزئة SHA-256 للسجل السابق، مما يجعل
    أي تعديل أو حذف قابلاً للكشف.

    Each entry includes a SHA-256 hash of the previous entry,
    making any modification or deletion detectable.

    الاستخدام / Usage:
        audit = AuditLogger()
        await audit.log("tool_call", "user_1", "execute", "browser_open", "success")
        is_valid = await audit.verify_integrity(log_file)
    """

    def __init__(self, log_dir: Optional[str] = None) -> None:
        """
        تهيئة سجل التدقيق — Initialize the audit logger.

        Args / المعاملات:
            log_dir: مجلد السجلات (الافتراضي: ~/.adam_prism/logs/audit/)
                     — Log directory (default: ~/.adam_prism/logs/audit/)
        """
        if log_dir is None:
            log_dir = os.path.expanduser("~/.adam_prism/logs/audit/")

        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # آخر تجزئة في السلسلة — Last hash in the chain
        self._last_hash: str = "GENESIS"  # البداية — Genesis block
        self._current_file: Optional[Path] = None
        self._current_date: Optional[str] = None

        # قفل للسلامة — Lock for thread safety
        self._lock = asyncio.Lock()

        # عداد الإحصائيات — Stats counter
        self._total_entries: int = 0

        # تهيئة الملف الحالي — Initialize current file
        self._ensure_log_file()

    # ─────────────────────────────────────────────
    # التسجيل / Logging
    # ─────────────────────────────────────────────

    async def log(
        self,
        event_type: str,
        actor: str,
        action: str,
        target: str,
        result: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        تسجيل حدث تدقيق — Log an audit event.

        Args / المعاملات:
            event_type: نوع الحدث (tool_call, auth, permission, config_change)
                        — Event type
            actor: من قام بالفعل — Who performed the action
            action: ماذا فعل — What was done
            target: على ماذا — What was affected
            result: النتيجة (success, denied, error) — Result
            metadata: بيانات إضافية — Additional metadata

        Returns / المخرجات:
            تجزئة السجل — Entry hash
        """
        entry = self._build_entry(event_type, actor, action, target, result, metadata)
        entry_hash = await self._write_entry(entry)
        return entry_hash

    def _build_entry(
        self,
        event_type: str,
        actor: str,
        action: str,
        target: str,
        result: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        بناء سجل التدقيق — Build an audit entry dict.
        """
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "epoch": time.time(),
            "event_type": event_type,
            "actor": actor,
            "action": action,
            "target": target,
            "result": result,
            "metadata": metadata or {},
            "prev_hash": self._last_hash,
        }

    async def _write_entry(self, entry: Dict[str, Any]) -> str:
        """
        كتابة سجل إلى الملف — Write an entry to the log file.

        Returns / المخرجات:
            تجزئة السجل الجديد — New entry hash
        """
        async with self._lock:
            # التحقق من تدوير الملف — Check for daily rotation
            self._ensure_log_file()

            # حساب التجزئة — Compute hash
            entry_str = json.dumps(entry, sort_keys=True, ensure_ascii=False)
            entry_hash = hashlib.sha256(entry_str.encode("utf-8")).hexdigest()

            # إضافة التجزئة للسجل — Add hash to entry
            entry["hash"] = entry_hash

            # كتابة السطر — Write the line
            line = json.dumps(entry, sort_keys=True, ensure_ascii=False)
            try:
                with open(self._current_file, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except OSError as exc:
                logger.error("Failed to write audit entry: %s", exc)
                raise

            # تحديث السلسلة — Update chain
            self._last_hash = entry_hash
            self._total_entries += 1

        logger.debug(
            "Audit: %s %s → %s [%s]",
            entry["actor"], entry["action"], entry["target"], entry["result"],
        )
        return entry_hash

    def _ensure_log_file(self) -> None:
        """
        التأكد من ملف السجل الحالي — Ensure current log file exists (daily rotation).
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if self._current_date == today and self._current_file is not None:
            return  # نفس اليوم — Same day

        # ملف جديد — New file for today
        self._current_date = today
        self._current_file = self._log_dir / f"audit-{today}.jsonl"

        # إذا كان الملف موجوداً، نقرأ آخر تجزئة — If file exists, read last hash
        if self._current_file.exists():
            last_hash = self._get_last_hash_from_file(self._current_file)
            if last_hash:
                self._last_hash = last_hash
            # else: ابقِ على التجزئة الحالية (ربما يوم جديد) — Keep current hash

    @staticmethod
    def _get_last_hash_from_file(filepath: Path) -> Optional[str]:
        """
        الحصول على آخر تجزئة من ملف — Get the last hash from a log file.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                last_line = None
                for line in f:
                    line = line.strip()
                    if line:
                        last_line = line

                if last_line:
                    entry = json.loads(last_line)
                    return entry.get("hash")
        except (OSError, json.JSONDecodeError):
            pass
        return None

    # ─────────────────────────────────────────────
    # التحقق من السلامة / Integrity Verification
    # ─────────────────────────────────────────────

    async def verify_integrity(self, log_file: Optional[str] = None) -> bool:
        """
        التحقق من سلامة سلسلة التجزئة — Verify the hash chain integrity.

        Args / المعاملات:
            log_file: مسار ملف السجل (الافتراضي: الملف الحالي) — Log file path

        Returns / المخرجات:
            True إذا كانت السلسلة سليمة — True if chain is intact
        """
        if log_file:
            filepath = Path(log_file)
        else:
            self._ensure_log_file()
            filepath = self._current_file

        if not filepath or not filepath.exists():
            logger.warning("Audit log file not found: %s", filepath)
            return False

        prev_hash = "GENESIS"
        line_num = 0
        errors: List[str] = []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    line_num += 1

                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError as exc:
                        errors.append(f"Line {line_num}: invalid JSON — {exc}")
                        continue

                    # التحقق من prev_hash — Verify prev_hash
                    stored_prev = entry.get("prev_hash", "")
                    if stored_prev != prev_hash:
                        errors.append(
                            f"Line {line_num}: prev_hash mismatch — "
                            f"expected {prev_hash[:16]}... got {stored_prev[:16]}..."
                        )

                    # إعادة حساب التجزئة — Recompute hash
                    stored_hash = entry.get("hash", "")
                    # إزالة التجزئة من القاموس لإعادة الحساب — Remove hash for recalculation
                    entry_copy = {k: v for k, v in entry.items() if k != "hash"}
                    recomputed = hashlib.sha256(
                        json.dumps(entry_copy, sort_keys=True, ensure_ascii=False).encode("utf-8")
                    ).hexdigest()

                    if recomputed != stored_hash:
                        errors.append(
                            f"Line {line_num}: hash mismatch — "
                            f"expected {recomputed[:16]}... got {stored_hash[:16]}..."
                        )

                    prev_hash = stored_hash

        except OSError as exc:
            logger.error("Failed to read audit log: %s", exc)
            return False

        if errors:
            for err in errors:
                logger.error("Integrity check FAILED: %s", err)
            return False

        logger.info("Integrity check passed — %d entries verified in %s", line_num, filepath.name)
        return True

    # ─────────────────────────────────────────────
    # البحث / Search
    # ─────────────────────────────────────────────

    async def search(
        self,
        query: Dict[str, str],
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        البحث في سجلات التدقيق — Search audit logs.

        Args / المعاملات:
            query: معايير البحث (مفاتيح وقيم يجب أن تتطابق)
                   — Search criteria (key-value pairs that must match)
            limit: الحد الأقصى للنتائج — Max results

        Returns / المخرجات:
            قائمة بالسجلات المتطابقة — List of matching entries
        """
        results: List[Dict[str, Any]] = []

        # البحث في جميع ملفات السجلات — Search all log files
        log_files = sorted(self._log_dir.glob("audit-*.jsonl"), reverse=True)

        for log_file in log_files:
            if len(results) >= limit:
                break

            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if len(results) >= limit:
                            break
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        # تطابق معايير البحث — Match search criteria
                        match = all(
                            str(entry.get(k, "")).lower() == v.lower()
                            for k, v in query.items()
                        )
                        if match:
                            results.append(entry)

            except OSError:
                continue

        return results[:limit]

    # ─────────────────────────────────────────────
    # دوال مساعدة / Helper Functions
    # ─────────────────────────────────────────────

    async def audit_tool_call(
        self,
        actor: str,
        tool_name: str,
        params: Dict[str, Any],
        result: str,
        allowed: bool = True,
    ) -> str:
        """
        تسجيل استدعاء أداة — Audit a tool call.

        Args / المعاملات:
            actor: من استدعى الأداة — Who called the tool
            tool_name: اسم الأداة — Tool name
            params: معاملات الاستدعاء — Call parameters
            result: النتيجة — Result
            allowed: هل سُمح بالاستدعاء؟ — Was the call allowed?

        Returns / المخرجات:
            تجزئة السجل — Entry hash
        """
        return await self.log(
            event_type="tool_call",
            actor=actor,
            action="execute",
            target=tool_name,
            result="success" if allowed else "denied",
            metadata={
                "params": {k: str(v)[:200] for k, v in params.items()},
                "allowed": allowed,
            },
        )

    async def audit_permission(
        self,
        actor: str,
        permission: str,
        target: str,
        granted: bool,
        reason: str = "",
    ) -> str:
        """
        تسجيل قرار صلاحية — Audit a permission decision.

        Args / المعاملات:
            actor: من طلب الصلاحية — Who requested permission
            permission: نوع الصلاحية — Permission type
            target: الهدف — Target resource
            granted: هل مُنحت الصلاحية؟ — Was permission granted?
            reason: السبب — Reason

        Returns / المخرجات:
            تجزئة السجل — Entry hash
        """
        return await self.log(
            event_type="permission",
            actor=actor,
            action="grant" if granted else "deny",
            target=target,
            result="granted" if granted else "denied",
            metadata={"permission": permission, "reason": reason},
        )

    async def audit_auth(
        self,
        actor: str,
        action: str,
        target: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        تسجيل حدث مصادقة — Audit an authentication event.

        Args / المعاملات:
            actor: من حاول المصادقة — Who attempted auth
            action: نوع الفعل (login, token_refresh, api_key_check)
                    — Action type
            target: الهدف — Target
            success: هل نجحت المصادقة؟ — Was auth successful?
            metadata: بيانات إضافية — Additional metadata

        Returns / المخرجات:
            تجزئة السجل — Entry hash
        """
        return await self.log(
            event_type="auth",
            actor=actor,
            action=action,
            target=target,
            result="success" if success else "failed",
            metadata=metadata or {},
        )

    async def audit_config_change(
        self,
        actor: str,
        config_key: str,
        old_value: Any,
        new_value: Any,
    ) -> str:
        """
        تسجيل تغيير إعدادات — Audit a configuration change.

        Args / المعاملات:
            actor: من غيّر الإعدادات — Who changed the config
            config_key: مفتاح الإعداد — Config key
            old_value: القيمة القديمة — Old value
            new_value: القيمة الجديدة — New value

        Returns / المخرجات:
            تجزئة السجل — Entry hash
        """
        return await self.log(
            event_type="config_change",
            actor=actor,
            action="update",
            target=config_key,
            result="applied",
            metadata={
                "old_value": str(old_value)[:500],
                "new_value": str(new_value)[:500],
            },
        )

    # ─────────────────────────────────────────────
    # إحصائيات / Stats
    # ─────────────────────────────────────────────

    async def get_stats(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات سجل التدقيق — Get audit logger statistics.

        Returns / المخرجات:
            إحصائيات — Stats dict
        """
        log_files = list(self._log_dir.glob("audit-*.jsonl"))
        total_size = sum(f.stat().st_size for f in log_files if f.exists())

        return {
            "log_dir": str(self._log_dir),
            "log_files": len(log_files),
            "total_entries": self._total_entries,
            "total_size_bytes": total_size,
            "current_file": str(self._current_file) if self._current_file else None,
            "last_hash": self._last_hash[:16] + "...",
        }
