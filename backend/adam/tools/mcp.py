"""
Adam Prism — MCP (Model Context Protocol) Integration
========================================================
يربط آدم بآلاف الأدوات عبر خوادم MCP القياسية.

[FIXES in this version]
1. إصلاح dead code بعد raise ValueError في add_server (خط 133-134)
2. إضافة تحقق من صحة اسم الخادم
3. تسجيل كل عمليات الإضافة
"""

import os
import sys
import logging
import json
from contextlib import AsyncExitStack
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

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

    def __init__(self, name: str, command: str, args: List[str] = None, env: Dict[str, str] = None):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.session: Optional[ClientSession] = None
        self.tools: List[MCPTool] = []
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
            logger.info(f"MCP '{self.name}' connected — {len(self.tools)} tools: {[t.name for t in self.tools]}")
        except Exception as e:
            logger.warning(f"MCP '{self.name}' connection failed: {e}")
            await self._cleanup()
            raise

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict:
        """استدعاء أداة على الخادم"""
        if not self._connected or not self.session:
            return {"success": False, "error": "MCP not connected"}
        try:
            result = await self.session.call_tool(tool_name, arguments=arguments or {})
            blocks = []
            for block in result.content:
                if hasattr(block, "text"):
                    blocks.append(block.text)
                elif hasattr(block, "data"):
                    blocks.append(f"[data: {len(block.data)} bytes]")
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
        try:
            await self._exit_stack.aclose()
        except Exception:
            pass


class MCPManager:
    """مدير اتصالات MCP — يدير خوادم متعددة"""

    # الأوامر المسموحة لخوادم MCP — منع تنفيذ أوامر تعسفية
    ALLOWED_MCP_COMMANDS = {"npx", "node", "python3", "python", "uvx"}

    def __init__(self):
        self.connections: Dict[str, MCPConnection] = {}
        self._tool_map: Dict[str, str] = {}  # tool_name → connection name

    async def add_server(self, name: str, command: str, args: List[str] = None, env: Dict[str, str] = None):
        """يضيف خادم MCP جديد — مع التحقق من الأمر

        [FIX] تم نقل إنشاء MCPConnection قبل raise ValueError
        كان الكود القديم يضع conn = MCPConnection بعد raise ValueError
        مما يجعله unreachable code — خوادم MCP لم تكن تُضاف أبداً!
        """
        import shlex

        # [FIX] التحقق من صحة اسم الخادم
        if not name or len(name) > 50:
            raise ValueError(f"MCP server name must be between 1 and 50 characters")

        # [FIX] منع الأسماء المحجوزة
        reserved_names = {"admin", "system", "internal", "__init__"}
        if name.lower() in reserved_names:
            raise ValueError(f"MCP server name '{name}' is reserved")

        # استخراج الأمر الأساسي
        try:
            parts = shlex.split(command)
        except ValueError:
            raise ValueError(f"Invalid MCP command: {command}")
        base_cmd = parts[0] if parts else command

        # التحقق من القائمة البيضاء
        base_basename = os.path.basename(base_cmd)
        if base_basename not in self.ALLOWED_MCP_COMMANDS:
            raise ValueError(f"MCP command not allowed: {base_basename} — available commands: {', '.join(sorted(self.ALLOWED_MCP_COMMANDS))}")

        # [FIX] إنشاء الاتصال BEFORE أي raise — كان هذا هو الخطأ الأساسي
        conn = MCPConnection(name, command, args, env)
        self.connections[name] = conn
        try:
            await conn.connect()
            for tool in conn.tools:
                self._tool_map[tool.name] = name
            logger.info(f"MCP server '{name}' added with {len(conn.tools)} tools")
        except Exception as e:
            # لو الاتصال فشل، نشيله من connections بس مسجلين الخطأ
            logger.warning(f"MCP server '{name}' added but connection failed: {e}")
            # لا نرفع الاستثناء — الخادم موجود وممكن يتصل لاحقاً

    async def initialize(self, servers: List[Dict] = None):
        """تهيئة خوادم MCP من config"""
        for cfg in (servers or []):
            await self.add_server(
                name=cfg["name"],
                command=cfg["command"],
                args=cfg.get("args", []),
                env=cfg.get("env"),
            )

    async def call_tool(self, tool_name: str, arguments: Dict = None) -> Dict:
        """استدعاء أداة من أي خادم"""
        conn_name = self._tool_map.get(tool_name)
        if not conn_name:
            return {"success": False, "error": f"Tool '{tool_name}' not found in any MCP server"}
        conn = self.connections.get(conn_name)
        if not conn:
            return {"success": False, "error": f"Server '{conn_name}' not connected"}
        return await conn.call_tool(tool_name, arguments)

    def get_all_tools(self) -> List[Dict]:
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
