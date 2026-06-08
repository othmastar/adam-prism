"""
Adam Prism — MCP (Model Context Protocol) Integration
========================================================
يربط آدم بآلاف الأدوات عبر خوادم MCP القياسية.
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
            logger.info(f"✅ MCP '{self.name}' متصل — {len(self.tools)} أداة: {[t.name for t in self.tools]}")
        except Exception as e:
            logger.warning(f"⚠️ MCP '{self.name}' فشل الاتصال: {e}")
            await self._cleanup()
            raise

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict:
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
        try:
            await self._exit_stack.aclose()
        except Exception:
            pass


class MCPManager:
    """مدير اتصالات MCP — يدير خوادم متعددة"""

    def __init__(self):
        self.connections: Dict[str, MCPConnection] = {}
        self._tool_map: Dict[str, str] = {}  # tool_name → connection name

    async def add_server(self, name: str, command: str, args: List[str] = None, env: Dict[str, str] = None):
        """يضيف خادم MCP جديد"""
        conn = MCPConnection(name, command, args, env)
        self.connections[name] = conn
        try:
            await conn.connect()
            for tool in conn.tools:
                self._tool_map[tool.name] = name
        except Exception:
            pass

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
            return {"success": False, "error": f"أداة '{tool_name}' مش موجودة في أي خادم MCP"}
        conn = self.connections.get(conn_name)
        if not conn:
            return {"success": False, "error": f"خادم '{conn_name}' مش متصل"}
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
