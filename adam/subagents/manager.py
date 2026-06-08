"""
Adam Prism — Subagent Manager
===============================
يدير جلسات الوكلاء الفرعيين: spawn, list, chat, kill, teams.
"""

import logging
from typing import Dict, Any, List, Optional

from adam.subagents.session import SubagentSession

logger = logging.getLogger("adam_prism.subagents")


class SubagentManager:
    """مدير الوكلاء الفرعيين — individuals + teams"""

    def __init__(self, engine=None):
        self.engine = engine
        self._sessions: Dict[str, SubagentSession] = {}
        self._team_manager = None

    @property
    def teams(self):
        """TeamManager (lazy init)"""
        if self._team_manager is None:
            from adam.subagents.teams import TeamManager
            self._team_manager = TeamManager(self.engine)
        return self._team_manager

    def spawn(self, name: str, config: Dict[str, Any] = None) -> SubagentSession:
        """إنشاء وكيل فرعي جديد"""
        session = SubagentSession(name=name, engine=self.engine, config=config)
        self._sessions[session.id] = session
        logger.info(f"🧬 Subagent spawned: '{name}' ({session.id})")
        return session

    def get(self, session_id: str) -> Optional[SubagentSession]:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        if session:
            logger.info(f"🗑 Subagent removed: '{session.name}' ({session_id})")
            return True
        return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        return [s.get_status() for s in self._sessions.values()]

    def remove_all(self):
        self._sessions.clear()
        logger.info("All subagents removed")
