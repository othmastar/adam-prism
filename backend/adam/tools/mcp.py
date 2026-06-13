"""
Adam Prism — MCP (Model Context Protocol) Integration — HARDENED v3
=====================================================================
يربط آدم بآلاف الأدوات عبر خوادم MCP القياسية.

[SECURITY FIXES v2]
1. إصلاح خلل حرج: كود غير قابل للوصول بعد raise ValueError
2. قائمة بيضاء للأوامر المسموحة
3. تسجيل كل إضافة خادم جديد
4. حد أقصى لعدد خوادم MCP

[FIX v3 — BUG FIX]
5. Failed MCP connections are now cleaned up from self.connections
   Previously, failed connections were stored but never removed,
   causing memory leaks and stale connection references.
"""

import logging
import os
from contextlib import AsyncExitStack, suppress
from dataclasses import dataclass
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger("adam_prism.mcp")


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict
    server: str


class MCPConnection:
    """اتصال بخادم MCP واحد"""

    def __init__(self, name: str, command: str, args: list[str] | None = None, env: dict[str, str] | None = None):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.session: ClientSession | None = None
        self.tools: list[MCPTool] = []
        self._exit_stack = AsyncExitStack()
        self._connected = False

    async def connect(self):
        """تشغيل الخادم والاتصال به"""
        if self._connected:
            return
        try:
            full_env = {**os.environ, **self.env} if self.env else None
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=full_env,
            )
            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            self.session = await self._exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await self.session.initialize()
            # اكتشاف الأدوات
            response = await self.session.list_tools()
            self.tools = [
                MCPTool(
                    name=tool.name,
                    description=tool.description or "",
                    input_schema=tool.inputSchema or {},
                    server=self.name,
                )
                for tool in response.tools
            ]
            self._connected = True
            logger.info(f"MCP '{self.name}' متصل — {len(self.tools)} أداة: {[t.name for t in self.tools]}")
        except Exception as e:
            logger.warning(f"MCP '{self.name}' تعذر الاتصال: {e}")
            await self._cleanup()
            raise

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict:
        """استدعاء أداة على الخادم"""
        if not self._connected or not self.session:
            return {"success": False, "error": "MCP غير متصل"}
        try:
            result = await self.session.call_tool(tool_name, arguments=arguments or {})
            blocks = []
            for block in result.content:
                if hasattr(block, "text"):
                    blocks.append(block.text)
                elif hasattr(block, "data"):
                    blocks.append(f"[بيانات: {len(block.data)} بايت]")
                else:
                    blocks.append(str(block))
            return {"success": True, "data": "\n".join(blocks)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def disconnect(self):
        """قطع الاتصال وتنظيف الموارد"""
        self._connected = False
        await self._cleanup()

    async def _cleanup(self):
        with suppress(Exception):
            await self._exit_stack.aclose()


class MCPManager:
    """مدير اتصالات MCP — يدير خوادم متعددة"""

    # الأوامر المسموحة لخوادم MCP — منع تنفيذ أوامر تعسفية
    ALLOWED_MCP_COMMANDS = {"npx", "node", "python3", "python", "uvx"}

    # [FIX v2] حد أقصى لعدد خوادم MCP
    MAX_MCP_SERVERS = int(os.environ.get("ADAM_MAX_MCP_SERVERS", "10"))

    def __init__(self):
        self.connections: dict[str, MCPConnection] = {}
        self._tool_map: dict[str, str] = {}  # tool_name → connection name

    async def add_server(self, name: str, command: str, args: list[str] | None = None, env: dict[str, str] | None = None):
        """يضيف خادم MCP جديد — مع التحقق من الأمر"""
        import shlex

        # [FIX v2] التحقق من عدد الخوادم
        if len(self.connections) >= self.MAX_MCP_SERVERS:
            raise ValueError(f"عدد خوادم MCP وصل للحد الأقصى ({self.MAX_MCP_SERVERS})")

        # [FIX v2] التحقق من اسم الخادم
        if not name or len(name) > 50:
            raise ValueError("اسم خادم MCP لازم يكون بين 1 و 50 حرف")

        # استخراج الأمر الأساسي
        try:
            parts = shlex.split(command)
        except ValueError:
            raise ValueError(f"أمر MCP غير صالح: {command}")
        base_cmd = parts[0] if parts else command

        # التحقق من القائمة البيضاء
        base_basename = os.path.basename(base_cmd)
        if base_basename not in self.ALLOWED_MCP_COMMANDS:
            raise ValueError(
                f"أمر MCP غير مسموح: {base_basename} — "
                f"الأوامر المتاحة: {', '.join(sorted(self.ALLOWED_MCP_COMMANDS))}"
            )

        # [FIX] كان فيه raise ValueError فوق وده بيمنع إنشاء الاتصال
        # الآن الإنشاء بيحصل بعد التحقح فقط
        conn = MCPConnection(name, command, args, env)
        self.connections[name] = conn
        try:
            await conn.connect()
            for tool in conn.tools:
                self._tool_map[tool.name] = name
            logger.warning(f"MCP server added: name={name}, command={command}, tools={len(conn.tools)}")
        except Exception as e:
            # [FIX v3] Remove failed connections from self.connections
            # Previously, failed connections were stored but never cleaned up
            # This caused memory leaks and stale connection references
            self.connections.pop(name, None)
            # Also remove any tool mappings for this failed connection
            tools_to_remove = [t_name for t_name, t_conn in self._tool_map.items() if t_conn == name]
            for t_name in tools_to_remove:
                self._tool_map.pop(t_name, None)
            logger.warning(f"MCP server '{name}' connection failed, removed from connections: {e}")

    async def initialize(self, servers: list[dict] | None = None):
        """تهيئة خوادم MCP من config"""
        for cfg in (servers or []):
            await self.add_server(
                name=cfg["name"],
                command=cfg["command"],
                args=cfg.get("args", []),
                env=cfg.get("env"),
            )

    async def call_tool(self, tool_name: str, arguments: dict | None = None) -> dict:
        """استدعاء أداة من أي خادم"""
        conn_name = self._tool_map.get(tool_name)
        if not conn_name:
            return {"success": False, "error": f"أداة '{tool_name}' مش موجودة في أي خادم MCP"}
        conn = self.connections.get(conn_name)
        if not conn:
            return {"success": False, "error": f"خادم '{conn_name}' مش متصل"}
        return await conn.call_tool(tool_name, arguments)

    def get_all_tools(self) -> list[dict]:
        """كل الأدوات المتاحة من كل الخوادم"""
        tools = []
        for conn in self.connections.values():
            for tool in conn.tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                    "server": tool.server,
                })
        return tools

    def is_available(self, tool_name: str) -> bool:
        return tool_name in self._tool_map

    async def disconnect_all(self):
        """قطع كل الاتصالات"""
        for conn in self.connections.values():
            await conn.disconnect()
        self.connections.clear()
        self._tool_map.clear()
