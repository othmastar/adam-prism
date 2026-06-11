"""
Adam Prism Engine Tools - تنفيذ الأدوات
========================================
Tool dispatcher + 14 handler methods split across sub-modules.
"""

import os
import re
import json
import logging
from typing import Optional, Dict, List, Any

from core.permissions import classify_tool, log_permission
from adam.engine.generate import AdamPrismEngineGenerate
from adam.engine.tools.browser import BrowserToolsMixin
from adam.engine.tools.system_tools import SystemToolsMixin
from adam.engine.tools.file_ops import FileOpsMixin
from adam.engine.tools.knowledge import KnowledgeMixin
from adam.engine.tools.shell import ShellToolsMixin
from adam.engine.tools.memory_ops import MemoryToolsMixin
from adam.engine.tools.planning import PlanningMixin

logger = logging.getLogger("adam_prism.core")


class AdamPrismEngineTools(
    PlanningMixin, MemoryToolsMixin, ShellToolsMixin,
    KnowledgeMixin, FileOpsMixin, SystemToolsMixin,
    BrowserToolsMixin, AdamPrismEngineGenerate,
):
    """
    Mixin: tool dispatcher + 14 handler methods.
    """

    def _parse_tool_request(self, text: str) -> Optional[Dict]:
        func_pattern = r'<\|?tool_call\|?>\s*<function=(\w+)>(.*?)</function>\s*<\|?/?tool_call\|?>'
        func_match = re.search(func_pattern, text, re.DOTALL)
        if func_match:
            tool_name = func_match.group(1)
            params_block = func_match.group(2)
            params = {}
            for param_match in re.finditer(r'<parameter=(\w+)>(.*?)</parameter>', params_block, re.DOTALL):
                params[param_match.group(1)] = param_match.group(2).strip()
            return {"_tool": tool_name, "params": params}

        tc_pattern = r'<\|?tool_call\|?>\s*call:(\w+)\s*\{([^}]*)\}\s*<\|?/?tool_call\|?>'
        tc_match = re.search(tc_pattern, text, re.DOTALL)
        if tc_match:
            tool_name = tc_match.group(1)
            params_str = tc_match.group(2).strip()
            params = {}
            if params_str:
                try:
                    params = json.loads("{" + params_str + "}")
                except json.JSONDecodeError:
                    for kv in params_str.split(","):
                        if ":" in kv:
                            k, v = kv.split(":", 1)
                            k = k.strip().strip('"').strip("'")
                            v = v.strip().strip('"').strip("'")
                            params[k] = v
            return {"_tool": tool_name, "params": params}

        lines = text.strip().split("\n")
        for i in range(len(lines) - 1, max(len(lines) - 5, 0) - 1, -1):
            line = lines[i].strip()
            try:
                parsed = json.loads(line)
                if "_tool" in parsed:
                    return parsed
            except (json.JSONDecodeError, ValueError):
                continue

        json_pattern = r'\{\s*"_tool"\s*:\s*"[^"]+"\s*,\s*"params"\s*:\s*\{.*?\}\s*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None

    async def _execute_tool(self, tool_name: str, params: Dict) -> Dict:
        result = {"success": False, "error": "أداة غير معروفة"}

        allowed, tool_name, params = await self._tool_check_permissions(tool_name, params)
        if not allowed:
            return result

        BROWSER = ("browser_open", "browser_fetch", "browser_click", "browser_type", "browser_read", "screenshot")
        MOUSE = ("mouse_click", "mouse_move", "mouse_scroll", "mouse_drag", "mouse_position")
        KEYBOARD = ("keyboard_type", "keyboard_press", "keyboard_hotkey")
        CLIPBOARD = ("clipboard_read", "clipboard_write")
        SCREEN = ("screen_info", "screen_ocr")
        WINDOW = ("window_focus", "window_list")
        MEMORY = ("memory_store", "memory_recall", "memory_reflect")

        if tool_name in BROWSER:
            result = await self._tool_browser(tool_name, params)
        elif tool_name in MOUSE:
            result = await self._tool_mouse(tool_name, params)
        elif tool_name in KEYBOARD:
            result = await self._tool_keyboard(tool_name, params)
        elif tool_name in CLIPBOARD:
            result = await self._tool_clipboard(tool_name, params)
        elif tool_name in SCREEN:
            result = await self._tool_screen(tool_name, params)
        elif tool_name in WINDOW:
            result = await self._tool_window(tool_name, params)
        elif tool_name == "disk_space":
            result = await self._tool_disk(params)
        elif tool_name in ("file_read", "file_write", "file_download"):
            result = await self._tool_file(tool_name, params)
        elif tool_name == "search_knowledge":
            result = await self._tool_knowledge(params)
        elif tool_name in ("request_permission", "check_preferences", "notebook_update_profile"):
            result = await self._tool_preferences(tool_name, params)
        elif tool_name in ("shell", "python_exec"):
            result = await self._tool_shell(tool_name, params)
        elif tool_name in MEMORY:
            result = await self._tool_memory(tool_name, params)
        elif tool_name == "tool_planning":
            result = await self._tool_planning(params)

        if self.plugins:
            result = await self.plugins.run_after_tool({"type": tool_name, "params": params}, result)
        return result

    async def _tool_check_permissions(self, tool_name: str, params: Dict) -> tuple:
        if self.security_guard:
            try:
                perm_verdict = await self.security_guard.check_tool_call(tool_name, params)
                if perm_verdict.action.value == "block":
                    return False, tool_name, params
            except Exception as e:
                logger.warning(f"Tool permission check error: {e}")

        if tool_name != "request_permission":
            cat = classify_tool(tool_name)
            need = self.permission.needs_permission(cat)
            if need:
                log_permission("blocked (deferred)", tool_name, cat,
                               "يحتاج صلاحية (phase 1b not activated)", need, "deferred")

        if self.plugins:
            action_check = await self.plugins.run_before_tool({"type": tool_name, "params": params})
            if action_check is None:
                return False, tool_name, params
            tool_name = action_check.get("type", tool_name)
            params = action_check.get("params", params)

        return True, tool_name, params

    @property
    def _local_bin(self) -> str:
        return self.config.get("local_bin", os.path.expanduser("~/.local/bin"))

    @property
    def _data_dir(self) -> str:
        return self.config.get("data_dir", os.path.expanduser("~/.local/share/adam"))
