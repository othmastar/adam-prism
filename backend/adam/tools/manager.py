"""
Adam Prism — Tool Manager
============================
يدير كل الأدوات: browser + computer + MCP + file + shell
"""

import os
import json
import logging
import subprocess
from typing import Dict, Any, Optional, List

from adam.eyes.browser import Browser
from adam.tools.computer import ComputerToolManager
from adam.tools.mcp import MCPManager
from adam.core.permissions import classify_tool

logger = logging.getLogger("adam_prism.tools")


class ToolManager:
    """مدير الأدوات — يوجّه الاستدعاءات للمتعامل المناسب"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.browser = Browser(self.config.get("browser", {}))
        self.computer = ComputerToolManager()
        self.mcp = MCPManager()
        self.action_log: List[Dict] = []

    async def initialize(self):
        """تهيئة كل الأدوات"""
        await self.browser.initialize()
        mcp_servers = self.config.get("mcp_servers", [])
        if mcp_servers:
            await self.mcp.initialize(mcp_servers)

    async def execute_action(self, action: Dict) -> Dict:
        action_type = action.get("type", "")
        self.action_log.append({"type": action_type, "timestamp": __import__("time").time()})

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

    def get_mcp_tools(self) -> List[Dict]:
        return self.mcp.get_all_tools()

    async def add_mcp_server(self, name: str, command: str, args: List[str] = None, env: Dict[str, str] = None):
        await self.mcp.add_server(name, command, args, env)

    async def _exec_browser(self, action: Dict) -> Dict:
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

    async def _exec_file(self, action: Dict) -> Dict:
        at = action.get("type")
        try:
            if at == "file_read":
                path = action.get("path", "")
                if not path:
                    return {"success": False, "error": "مفيش path"}
                with open(path) as f:
                    return {"success": True, "data": f.read()}
            elif at == "file_write":
                path = action.get("path", "")
                content = action.get("content", "")
                if not path:
                    return {"success": False, "error": "مفيش path"}
                with open(path, "w") as f:
                    f.write(content)
                return {"success": True}
            elif at == "disk_space":
                _df_path = os.environ.get("ADAM_WORKSPACE", os.path.expanduser("~"))
                r = subprocess.run(["df", "-h", _df_path],
                                  capture_output=True, text=True, timeout=5)
                return {"success": True, "data": r.stdout}
            return {"success": False, "error": f"File action unknown: {at}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_action_log(self, limit: int = 50) -> List[Dict]:
        return self.action_log[-limit:]
