"""
Adam Prism — Subagent Manager — HARDENED v2
===============================================
يدير جلسات الوكلاء الفرعيين: spawn, list, chat, kill, teams.

[SECURITY FIXES v2]
1. تحديد عدد الوكلاء الفرعيين
2. تسجيل كل عمليات الإنشاء
3. منع الأسماء الخطرة
4. [NEW] منع إنشاء وكيل بنفس الاسم
5. [NEW] تنظيف تلقائي للوكلاء الخاملين
"""

import logging
import os
import time
from typing import Any

from adam.subagents.session import SubagentSession

logger = logging.getLogger("adam_prism.subagents")

class SubagentManager:
    """مدير الوكلاء الفرعيين — individuals + teams"""

    # الحد الأقصى لعدد الوكلاء الفرعيين — قابل للتعديل عبر ADAM_MAX_SUBAGENTS
    MAX_SUBAGENTS = int(os.environ.get("ADAM_MAX_SUBAGENTS", "10"))

    # [NEW] مهلة الخمول بالثواني — الوكلاء الخاملين يتم حذفهم تلقائياً
    IDLE_TIMEOUT = int(os.environ.get("ADAM_SUBAGENT_IDLE_TIMEOUT", "3600"))  # ساعة

    def __init__(self, engine=None):
        self.engine = engine
        self._sessions: dict[str, SubagentSession] = {}
        self._team_manager = None

    @property
    def teams(self):
        """TeamManager (lazy init)"""
        if self._team_manager is None:
            from adam.subagents.teams import TeamManager
            self._team_manager = TeamManager(self.engine)
        return self._team_manager

    def spawn(self, name: str, config: dict[str, Any] | None = None) -> SubagentSession:
        """إنشاء وكيل فرعي جديد"""

        # التحقق من العدد الأقصى
        if len(self._sessions) >= self.MAX_SUBAGENTS:
            raise ValueError(f"عدد الوكلاء الفرعيين وصل للحد الأقصى ({self.MAX_SUBAGENTS})")

        # التحقق من صحة الاسم
        if not name or len(name) > 50:
            raise ValueError("اسم الوكيل لازم يكون بين 1 و 50 حرف")

        # منع الأسماء الخطرة
        _dangerous_names = ["admin", "root", "system", "adam", "core", "sudo", "daemon"]
        if name.lower() in _dangerous_names:
            raise ValueError(f"اسم الوكيل '{name}' محظور — اختر اسم آخر")

        # [NEW] منع إنشاء وكيل بنفس الاسم
        for session in self._sessions.values():
            if session.name == name:
                raise ValueError(f"وكيل فرعي بالاسم '{name}' موجود بالفعل — اختر اسم آخر")

        session = SubagentSession(name=name, engine=self.engine, config=config)
        self._sessions[session.id] = session

        # تسجيل عملية الإنشاء مع تفاصيل أمنية
        logger.warning(f"Subagent spawned: '{name}' ({session.id}) — tools_enabled={session.tools_enabled}")
        return session

    def get(self, session_id: str) -> SubagentSession | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        if session:
            logger.info(f"Subagent removed: '{session.name}' ({session_id})")
            return True
        return False

    def list_sessions(self) -> list[dict[str, Any]]:
        return [s.get_status() for s in self._sessions.values()]

    def remove_all(self):
        self._sessions.clear()
        logger.info("All subagents removed")

    # [NEW] تنظيف الوكلاء الخاملين
    def cleanup_idle(self) -> int:
        """حذف الوكلاء الخاملين — يرجع عدد المحذوفين"""
        now = time.time()
        to_remove = []
        for sid, session in self._sessions.items():
            idle_seconds = now - session.last_active.timestamp()
            if idle_seconds > self.IDLE_TIMEOUT:
                to_remove.append(sid)
        for sid in to_remove:
            self.remove(sid)
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} idle subagents")
        return len(to_remove)
