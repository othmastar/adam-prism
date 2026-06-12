"""
Adam Prism — Permission Manager (Phase 1b) — HARDENED
======================================================
يدير صلاحيات تنفيذ الأدوات حسب التصنيف والمستوى.

[SECURITY FIX v2]
1. الأذونات الخطيرة أصبحت "always-ask" بدلاً من "auto-allow"
2. إضافة تصنيفات أمنية واضحة
3. دعم وضع الإنتاج (ADAM_PRODUCTION=1) يغلّظ الصلاحيات تلقائياً
"""

import json
import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("adam_prism.permissions")

PERMISSION_LOG = Path(os.environ.get("ADAM_PERMISSION_LOG", "/tmp/adam_permissions.log"))

# هل نحن في وضع الإنتاج؟
IS_PRODUCTION = os.environ.get("ADAM_PRODUCTION", "0") == "1"

# تصنيفات الصلاحيات والتوصيف
# [FIX v2] الأذونات الخطيرة أصبحت "always-ask" في كل الأوضاع
# في وضع التطوير: الأذونات البسيطة "auto-allow"
# في وضع الإنتاج: كل شيء "always-ask" ما عدا القراءة البسيطة
PERMISSION_CATEGORIES = {
    "shell.read": {
        "default": "auto-allow" if not IS_PRODUCTION else "ask-once",
        "description": "أوامر قراءة (ls, cat, df)",
        "risk": "low"
    },
    "shell.write": {
        "default": "ask-once",
        "description": "أوامر كتابة (touch, mkdir, cp في الورك سبيس)",
        "risk": "medium"
    },
    "shell.dangerous": {
        "default": "always-ask",
        "description": "أوامر خطيرة (rm, sudo, chmod, kill)",
        "risk": "critical"
    },
    "python": {
        "default": "ask-once",
        "description": "تشغيل كود Python",
        "risk": "high"
    },
    "file.read": {
        "default": "auto-allow" if not IS_PRODUCTION else "ask-once",
        "description": "قراءة ملفات في الورك سبيس",
        "risk": "low"
    },
    "file.write": {
        "default": "ask-once",
        "description": "كتابة ملفات في الورك سبيس",
        "risk": "medium"
    },
    "file.write.system": {
        "default": "always-ask",
        "description": "كتابة خارج الورك سبيس",
        "risk": "critical"
    },
    "browser": {
        "default": "auto-allow" if not IS_PRODUCTION else "ask-once",
        "description": "فتح متصفح وتصفح",
        "risk": "low"
    },
    "mouse": {
        "default": "ask-once",
        "description": "تحريك الماوس والنقر",
        "risk": "medium"
    },
    "keyboard": {
        "default": "ask-once",
        "description": "كتابة عبر لوحة المفاتيح",
        "risk": "high"
    },
    "clipboard": {
        "default": "always-ask",
        "description": "قراءة/كتابة الحافظة — قد تحتوي بيانات حساسة",
        "risk": "high"
    },
    "screen": {
        "default": "ask-once",
        "description": "تصوير أو قراءة الشاشة",
        "risk": "medium"
    },
    "window": {
        "default": "ask-once",
        "description": "التحكم في النوافذ",
        "risk": "medium"
    },
    "knowledge": {
        "default": "auto-allow",
        "description": "البحث في قاعدة المعرفة",
        "risk": "low"
    },
    "notebook": {
        "default": "auto-allow" if not IS_PRODUCTION else "ask-once",
        "description": "قراءة/كتابة النوت بوك",
        "risk": "low"
    },
    "mcp": {
        "default": "always-ask",
        "description": "استدعاء أدوات MCP خارجية",
        "risk": "high"
    },
    "subagent": {
        "default": "ask-once",
        "description": "إنشاء/إدارة وكلاء فرعيين",
        "risk": "medium"
    },
}

# أداة → تصنيف
TOOL_CATEGORY_MAP = {
    "shell": "shell.dangerous",
    "python_exec": "python",
    "file_read": "file.read",
    "file_write": "file.write",
    "file_delete": "shell.dangerous",
    "file_list": "file.read",
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


def get_risk_level(category: str) -> str:
    """[FIX v2] مستوى الخطورة للتصنيف"""
    return PERMISSION_CATEGORIES.get(category, {}).get("risk", "unknown")


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
        "risk": get_risk_level(category),
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
