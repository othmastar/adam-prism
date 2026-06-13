"""
Adam Prism — Tool Manager — HARDENED v2
============================================
يدير كل الأدوات: browser + computer + MCP + file + shell

[SECURITY FIXES v2]
1. sanitize_path لكل عمليات الملفات
2. تسجيل الأفعال مع تفاصيل أمنية
3. حد أقصى لحجم الكتابة
4. حماية عمليات الحذف والقائمة
5. [NEW] تسجيل مفصّل لكل عملية MCP
6. [NEW] تحقق إضافي من أسماء الملفات
"""

import logging
import os
import subprocess
from typing import Any

from adam.core.permissions import classify_tool, get_risk_level
from adam.eyes.browser import Browser
from adam.infrastructure import sanitize_path
from adam.tools.computer import ComputerToolManager
from adam.tools.mcp import MCPManager

logger = logging.getLogger("adam_prism.tools")


class ToolManager:
    """مدير الأدوات — يوجّه الاستدعاءات للمتعامل المناسب"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.browser = Browser(self.config.get("browser", {}))
        self.computer = ComputerToolManager()
        self.mcp = MCPManager()
        self.action_log: list[dict] = []

    async def initialize(self):
        """تهيئة كل الأدوات"""
        await self.browser.initialize()
        mcp_servers = self.config.get("mcp_servers", [])
        if mcp_servers:
            await self.mcp.initialize(mcp_servers)

    async def execute_action(self, action: dict) -> dict:
        action_type = action.get("type", "")

        # [FIX v2] تسجيل مفصّل مع مستوى الخطورة
        risk = get_risk_level(classify_tool(action_type))
        self.action_log.append({
            "type": action_type,
            "risk": risk,
            "timestamp": __import__("time").time(),
        })

        # تحذير للعمليات عالية الخطورة
        if risk in ("high", "critical"):
            logger.warning(f"High-risk action: {action_type} (risk={risk})")

        # Browser actions
        browser_actions = {"browser_open", "browser_fetch", "browser_click",
                           "browser_type", "browser_read", "screenshot"}
        if action_type in browser_actions:
            return await self._exec_browser(action)

        # Computer actions
        computer_actions = {"mouse_click", "mouse_move", "mouse_scroll", "mouse_drag", "mouse_position",
                            "keyboard_type", "keyboard_press", "keyboard_hotkey",
                            "clipboard_read", "clipboard_write",
                            "screen_info", "screen_ocr",
                            "window_focus", "window_list"}
        if action_type in computer_actions:
            return await self.computer.execute_action(action)

        # File actions
        if action_type.startswith("file_") or action_type == "disk_space":
            return await self._exec_file(action)

        # MCP tools
        if self.mcp.is_available(action_type):
            return await self.mcp.call_tool(action_type, action.get("params", {}))

        return {"success": False, "error": f"إجراء غير معروف: {action_type}"}

    def get_mcp_tools(self) -> list[dict]:
        return self.mcp.get_all_tools()

    async def add_mcp_server(self, name: str, command: str, args: list[str] | None = None, env: dict[str, str] | None = None):
        """[FIX v2] إضافة خادم MCP — مع تسجيل أمني مفصّل"""
        logger.warning(f"MCP server add request: name={name}, command={command}, args={args}")
        await self.mcp.add_server(name, command, args, env)

    async def _exec_browser(self, action: dict) -> dict:
        if not await self.browser.is_healthy():
            ok = await self.browser.initialize()
            if not ok:
                return {"success": False, "error": "Browser مش شغال"}
        at = action.get("type")
        if at == "browser_open":
            return await self.browser.open(action.get("url", ""))
        elif at == "browser_fetch":
            return await self.browser.fetch(action.get("url", ""))
        elif at == "browser_click":
            return await self.browser.click(action.get("selector", ""))
        elif at == "browser_type":
            return await self.browser.type_text(action.get("selector", ""), action.get("text", ""))
        elif at == "browser_read":
            return await self.browser.read()
        elif at == "screenshot":
            return await self.browser.screenshot()
        return {"success": False, "error": f"Browser action unknown: {at}"}

    async def _exec_file(self, action: dict) -> dict:
        at = action.get("type")
        try:
            if at == "file_read":
                path = action.get("path", "")
                if not path:
                    return {"success": False, "error": "مفيش path"}
                # [FIX] sanitize_path — منع الوصول لملفات النظام
                safe = sanitize_path(path)
                if not safe:
                    logger.warning(f"محاولة وصول لملف غير مصرح: {path}")
                    return {"success": False, "error": "مسار غير مصرح به"}
                # [FIX v2] تحقق إضافي من الاسم
                if ".." in path or path.startswith("/"):
                    logger.warning(f"مسار مشبوه: {path}")
                with open(safe) as f:
                    content = f.read()
                # [FIX v2] حد أقصى لحجم القراءة
                MAX_READ_SIZE = 5 * 1024 * 1024  # 5MB
                if len(content) > MAX_READ_SIZE:
                    content = content[:MAX_READ_SIZE]
                    logger.info(f"file_read truncated: {safe}")
                return {"success": True, "data": content}
            elif at == "file_write":
                path = action.get("path", "")
                content = action.get("content", "")
                if not path:
                    return {"success": False, "error": "مفيش path"}
                # [FIX] sanitize_path — منع الكتابة في مسارات غير مصرحة
                safe = sanitize_path(path)
                if not safe:
                    logger.warning(f"محاولة كتابة لملف غير مصرح: {path}")
                    return {"success": False, "error": "مسار غير مصرح به"}
                # [FIX] حد أقصى لحجم المحتوى — منع كتابة ملفات ضخمة
                MAX_WRITE_SIZE = 5 * 1024 * 1024  # 5MB
                if len(content) > MAX_WRITE_SIZE:
                    return {"success": False, "error": f"المحتوى كبير جداً (الحد: {MAX_WRITE_SIZE // 1024 // 1024}MB)"}
                with open(safe, "w") as f:
                    f.write(content)
                logger.info(f"file_write: {safe} ({len(content)} chars)")
                return {"success": True}
            elif at == "file_delete":
                # [FIX] إضافة حماية لعملية الحذف
                path = action.get("path", "")
                if not path:
                    return {"success": False, "error": "مفيش path"}
                safe = sanitize_path(path)
                if not safe:
                    logger.warning(f"محاولة حذف ملف غير مصرح: {path}")
                    return {"success": False, "error": "مسار غير مصرح به"}
                # [FIX v2] منع حذف ملفات مهمة
                _protected_extensions = {".py", ".json", ".env", ".yaml", ".yml", ".toml", ".cfg"}
                _, ext = os.path.splitext(safe)
                if ext.lower() in _protected_extensions:
                    logger.warning(f"محاولة حذف ملف محمي: {safe}")
                    return {"success": False, "error": f"لا يمكن حذف ملفات {ext} — محمية"}
                if os.path.exists(safe):
                    os.remove(safe)
                    logger.warning(f"file_delete: {safe}")
                    return {"success": True}
                return {"success": False, "error": "الملف مش موجود"}
            elif at == "file_list":
                # [FIX] إضافة حماية لعملية القائمة
                path = action.get("path", "")
                if not path:
                    path = os.environ.get("ADAM_WORKSPACE", os.path.expanduser("~"))
                safe = sanitize_path(path)
                if not safe:
                    logger.warning(f"محاولة قائمة مجلد غير مصرح: {path}")
                    return {"success": False, "error": "مسار غير مصرح به"}
                entries = []
                for entry in os.listdir(safe):
                    full = os.path.join(safe, entry)
                    entries.append({
                        "name": entry,
                        "is_dir": os.path.isdir(full),
                        "size": os.path.getsize(full) if os.path.isfile(full) else 0,
                    })
                return {"success": True, "data": entries}
            elif at == "disk_space":
                _df_path = os.environ.get("ADAM_WORKSPACE", os.path.expanduser("~"))
                r = subprocess.run(["df", "-h", _df_path],
                                  capture_output=True, text=True, timeout=5)
                return {"success": True, "data": r.stdout}
            return {"success": False, "error": f"File action unknown: {at}"}
        except Exception as e:
            logger.exception("file action error: {at} —")
            return {"success": False, "error": str(e)}

    def get_action_log(self, limit: int = 50) -> list[dict]:
        return self.action_log[-limit:]
