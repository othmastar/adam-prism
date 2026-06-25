"""
Adam Prism — Permission Manager (Phase 1b)
===========================================
يدير صلاحيات تنفيذ الأدوات حسب التصنيف والمستوى.

[FIXES in this version]
1. تغيير الافتراضي من auto-allow إلى always-ask للأدوات الخطرة
2. حفظ السجل في مسار دائم بدلاً من /tmp
3. إضافة تصنيفات جديدة: mcp, subagent, workflow
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("adam_prism.permissions")

# [FIX] مسار دائم للسجل بدلاً من /tmp — الذي يُفقد عند إعادة التشغيل
_DATA_DIR = os.environ.get("ADAM_DATA_DIR", os.path.join(os.path.expanduser("~"), ".adam_prism"))
PERMISSION_LOG = Path(_DATA_DIR) / "logs" / "permissions.log"

# تأكد من وجود المجلد
try:
    PERMISSION_LOG.parent.mkdir(parents=True, exist_ok=True)
except Exception:
    # Fallback to /tmp if home directory is not writable
    PERMISSION_LOG = Path("/tmp/adam_permissions.log")

# تصنيفات الصلاحيات والتوصيف
# [FIX] الأدوات الخطرة الآن تتطلب إذن (always-ask) بدلاً من auto-allow
PERMISSION_CATEGORIES = {
    "shell.read": {"default": "auto-allow", "description": "Read commands (ls, cat, df, ps)"},
    "shell.write": {"default": "once", "description": "Write commands (touch, mkdir, cp in workspace)"},
    "shell.dangerous": {"default": "always-ask", "description": "Dangerous commands (rm, sudo, chmod, kill)"},
    "python": {"default": "once", "description": "Execute Python code"},
    "file.read": {"default": "auto-allow", "description": "Read files in workspace"},
    "file.write": {"default": "once", "description": "Write files in workspace"},
    "file.write.system": {"default": "always-ask", "description": "Write outside workspace"},
    "file.delete": {"default": "always-ask", "description": "Delete files"},
    "browser": {"default": "once", "description": "Open and browse browser"},
    "mouse": {"default": "always-ask", "description": "Move and click mouse"},
    "keyboard": {"default": "always-ask", "description": "Type via keyboard"},
    "clipboard": {"default": "once", "description": "Read/write clipboard"},
    "screen": {"default": "once", "description": "Capture or read screen"},
    "window": {"default": "once", "description": "Control windows"},
    "knowledge": {"default": "auto-allow", "description": "Search knowledge base"},
    "notebook": {"default": "auto-allow", "description": "Read/write notebook"},
    "mcp": {"default": "always-ask", "description": "Execute MCP server tools"},
    "subagent": {"default": "once", "description": "Manage subagents"},
    "workflow": {"default": "once", "description": "Execute workflows"},
}

# أداة → تصنيف
TOOL_CATEGORY_MAP = {
    "shell": "shell.dangerous",
    "python_exec": "python",
    "file_read": "file.read",
    "file_write": "file.write",
    "file_delete": "file.delete",
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
    "mcp_call": "mcp",
    "subagent_spawn": "subagent",
    "subagent_chat": "subagent",
    "workflow_execute": "workflow",
}

def classify_tool(tool_name: str) -> str:
    return TOOL_CATEGORY_MAP.get(tool_name, "shell.dangerous")

def default_level(category: str) -> str:
    return PERMISSION_CATEGORIES.get(category, {}).get("default", "always-ask")

# [FIX H11] Map categories to risk levels
def get_risk_level(category: str) -> str:
    """Map a permission category to a risk level string.

    Risk levels: critical, high, medium, low
    """
    _RISK_MAP = {
        "shell.dangerous": "critical",
        "python": "high",
        "file": "high",
        "file.write": "high",
        "file.write.system": "critical",
        "file.delete": "critical",
        "browser": "medium",
        "mouse": "high",
        "keyboard": "high",
        "clipboard": "medium",
        "screen": "medium",
        "window": "medium",
        "knowledge": "low",
        "memory": "low",
        "notebook": "low",
        "shell.read": "low",
        "shell.write": "medium",
        "file.read": "low",
        "mcp": "high",
        "subagent": "medium",
        "workflow": "medium",
    }
    return _RISK_MAP.get(category, "high")

class PermissionState:
    """تتبع حالة الصلاحيات لكل جلسة"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.granted: dict[str, dict] = {}  # category → {level, expires}
        self.pending_request: dict | None = None

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

    def grant(self, category: str, level: str, duration: int | None = None):
        expires = (time.time() + duration) if duration else None
        self.granted[category] = {"level": level, "expires": expires}
        self.pending_request = None

    def deny(self, category: str):
        self.granted.pop(category, None)
        self.pending_request = None

    def needs_permission(self, category: str) -> str | None:
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
    except Exception:
        logger.exception("Failed to log permission:")
    return entry
