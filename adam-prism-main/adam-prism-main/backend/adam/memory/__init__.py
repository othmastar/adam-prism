"""
Adam Prism — Memory System
============================
Iron Memory: Hot Memory + Session Search + Unified Memory Manager.
- Hot Memory: MEMORY.md + USER.md في system prompt
- Session Search: FTS5 بحث نصي كامل في الجلسات
- Unified Memory Manager: 4 طبقات ذاكرة
"""

from .hot_memory import HotMemory, MemorySecurityScanner
from .session_search import SessionSearch
from .unified import UnifiedMemoryManager

__all__ = ["HotMemory", "MemorySecurityScanner", "SessionSearch", "UnifiedMemoryManager"]
