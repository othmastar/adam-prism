"""
Adam Prism — Permission Manager (Phase 1b)
===========================================
يدير صلاحيات تنفيذ الأدوات حسب التصنيف والمستوى.
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("adam_prism.permissions")

PERMISSION_LOG = Path("/tmp/adam_permissions.log")

# تصنيفات الصلاحيات والتوصيف
PERMISSION_CATEGORIES = {
    "shell.read": {"default": "auto-allow", "description": "أوامر قراءة (ls, cat, df, ps)"},
    "shell.write": {"default": "auto-allow", "description": "أوامر كتابة (touch, mkdir, cp في الورك سبيس)"},
    "shell.dangerous": {"default": "auto-allow", "description": "أوامر خطيرة (rm, sudo, chmod, kill)"},
    "python": {"default": "auto-allow", "description": "تشغيل كود Python"},
    "file.read": {"default": "auto-allow", "description": "قراءة ملفات في /mnt/Workspace"},
    "file.write": {"default": "auto-allow", "description": "كتابة ملفات في /mnt/Workspace"},
    "file.write.system": {"default": "auto-allow", "description": "كتابة خارج الورك سبيس"},
    "browser": {"default": "auto-allow", "description": "فتح متصفح وتصفح"},
    "mouse": {"default": "auto-allow", "description": "تحريك الماوس والنقر"},
    "keyboard": {"default": "auto-allow", "description": "كتابة عبر لوحة المفاتيح"},
    "clipboard": {"default": "auto-allow", "description": "قراءة/كتابة الحافظة"},
    "screen": {"default": "auto-allow", "description": "تصوير أو قراءة الشاشة"},
    "window": {"default": "auto-allow", "description": "التحكم في النوافذ"},
    "knowledge": {"default": "auto-allow", "description": "البحث في قاعدة المعرفة"},
    "notebook": {"default": "auto-allow", "description": "قراءة/كتابة النوت بوك"},
}

# أداة → تصنيف
TOOL_CATEGORY_MAP = {
    "shell": "shell.dangerous",
    "python_exec": "python",
    "file_read": "file.read",
    "file_write": "file.write",
    "file_download": "file.write",
    "disk_space": "shell.read",
    "browser_open": "browser",
    "browser_fetch": "browser",
    "browser_click": "browser",
    "browser_type": "browser",
    "browser_read": "browser",
    "screenshot": "screen",
    "mouse_click": "mouse",
    "mouse_move": "mouse",
    "mouse_scroll": "mouse",
    "mouse_drag": "mouse",
    "mouse_position": "mouse",
    "keyboard_type": "keyboard",
    "keyboard_press": "keyboard",
    "keyboard_hotkey": "keyboard",
    "clipboard_read": "clipboard",
    "clipboard_write": "clipboard",
    "screen_ocr": "screen",
    "screen_info": "screen",
    "window_focus": "window",
    "window_list": "window",
    "search_knowledge": "knowledge",
    "notebook_update_profile": "notebook",
    "request_permission": "notebook",
    "web_search": "browser",
}


def classify_tool(tool_name: str) -> str:
    return TOOL_CATEGORY_MAP.get(tool_name, "shell.dangerous")


def default_level(category: str) -> str:
    return PERMISSION_CATEGORIES.get(category, {}).get("default", "always-ask")


class PermissionState:
    """تتبع حالة الصلاحيات لكل جلسة"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.granted: Dict[str, dict] = {}  # category → {level, expires}
        self.pending_request: Optional[dict] = None

    def is_auto(self, category: str) -> bool:
        return default_level(category) == "auto-allow"

    def is_granted(self, category: str) -> bool:
        entry = self.granted.get(category)
        if not entry:
            return False
        if entry["expires"] and entry["expires"] < time.time():
            del self.granted[category]
            return False
        return True

    def grant(self, category: str, level: str, duration: Optional[int] = None):
        expires = (time.time() + duration) if duration else None
        self.granted[category] = {"level": level, "expires": expires}
        self.pending_request = None

    def deny(self, category: str):
        self.granted.pop(category, None)
        self.pending_request = None

    def needs_permission(self, category: str) -> Optional[str]:
        if self.is_auto(category):
            return None
        if self.is_granted(category):
            return None
        dl = default_level(category)
        return dl  # "once" or "always-ask"


def log_permission(action: str, tool: str, category: str, reason: str, level: str, verdict: str):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "tool": tool,
        "category": category,
        "reason": reason,
        "level": level,
        "verdict": verdict,
    }
    try:
        with open(PERMISSION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"فشل تسجيل الصلاحية: {e}")
    return entry
