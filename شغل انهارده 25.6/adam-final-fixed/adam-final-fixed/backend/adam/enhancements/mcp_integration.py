"""
Adam Prism — MCP Integration Enhancement
==========================================
يربط tools/mcp.py الموجود عندك بـ engine.

Functions:
- يضيف MCP tools للـ tool registry
- يسمح بإضافة MCP servers من API
- ينفذ MCP tools من chat
- lazy loading للـ connections

Integration:
    from adam.enhancements.mcp_integration import MCPManager
    mcp = MCPManager()
    await mcp.init()
    await mcp.add_server("filesystem", "npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"])
    tools = await mcp.list_tools()
    result = await mcp.execute_tool("filesystem", "read_file", {"path": "/tmp/test.txt"})
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("adam_prism.mcp_enhanced")


# ============================================================
# Data Classes
# ============================================================

@dataclass
class MCPTool:
    """أداة MCP."""
    name: str
    description: str
    input_schema: dict
    server: str  # اسم الـ MCP server
    full_name: str = ""  # server:tool_name

    def __post_init__(self):
        if not self.full_name:
            self.full_name = f"{self.server}:{self.name}"


@dataclass
class MCPServer:
    """MCP server connection."""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    connected: bool = False
    tools: list[MCPTool] = field(default_factory=list)
    session: Any = None
    _exit_stack: Any = None


# ============================================================
# MCP Manager
# ============================================================

class MCPManager:
    """مدير MCP servers — يتكامل مع tools/mcp.py."""

    def __init__(self, max_servers: int = 10, max_tools_per_call: int = 5):
        self.max_servers = max_servers
        self.max_tools_per_call = max_tools_per_call
        self._servers: dict[str, MCPServer] = {}
        self._lock = asyncio.Lock()
        self._available: bool | None = None
        self._tool_handlers: dict[str, MCPServer] = {}  # tool_name -> server

    async def init(self) -> bool:
        """يتحقق من توفر MCP library."""
        try:
            from mcp import ClientSession, StdioServerParameters  # noqa: F401
            from mcp.client.stdio import stdio_client  # noqa: F401
            self._available = True
            logger.info("MCP manager initialized")
            return True
        except ImportError:
            logger.warning(
                "mcp library not installed. Install with: pip install mcp"
            )
            self._available = False
            return False

    @property
    def available(self) -> bool:
        return self._available is True

    # ============================================================
    # Server Management
    # ============================================================

    async def add_server(
        self,
        name: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> bool:
        """يضيف MCP server جديد ويتصل به."""
        if not self.available:
            return False

        if name in self._servers:
            logger.warning(f"MCP server '{name}' already exists")
            return True

        if len(self._servers) >= self.max_servers:
            logger.error(f"Max MCP servers ({self.max_servers}) reached")
            return False

        async with self._lock:
            try:
                from mcp import ClientSession, StdioServerParameters
                from mcp.client.stdio import stdio_client
                import os

                full_env = {**os.environ, **(env or {})} if env else None
                server_params = StdioServerParameters(
                    command=command,
                    args=args or [],
                    env=full_env,
                )

                exit_stack = AsyncExitStack()
                await exit_stack.__aenter__()

                # تشغيل الـ server
                read, write = await exit_stack.enter_async_context(
                    stdio_client(server_params)
                )

                # إنشاء session
                session = await exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                await session.initialize()

                # جلب الأدوات
                tools_response = await session.list_tools()
                tools = [
                    MCPTool(
                        name=t.name,
                        description=t.description or "",
                        input_schema=t.inputSchema or {},
                        server=name,
                    )
                    for t in tools_response.tools
                ]

                server = MCPServer(
                    name=name, command=command,
                    args=args or [], env=env or {},
                    connected=True, tools=tools,
                    session=session, _exit_stack=exit_stack,
                )
                self._servers[name] = server

                # تسجيل الأدوات
                for tool in tools:
                    self._tool_handlers[tool.full_name] = server
                    self._tool_handlers[tool.name] = server  # بدون prefix

                logger.info(
                    f"MCP server '{name}' connected with {len(tools)} tools"
                )
                return True

            except Exception as e:
                logger.error(f"Failed to connect MCP server '{name}': {e}")
                return False

    async def remove_server(self, name: str) -> bool:
        """يفصل ويحذف MCP server."""
        async with self._lock:
            server = self._servers.pop(name, None)
            if not server:
                return False

            # شيل الـ tools بتاعته
            tools_to_remove = [
                t for t in list(self._tool_handlers.keys())
                if self._tool_handlers[t] is server
            ]
            for t in tools_to_remove:
                del self._tool_handlers[t]

            # اقفل الـ connection
            try:
                if server._exit_stack:
                    await server._exit_stack.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing MCP server '{name}': {e}")

            server.connected = False
            logger.info(f"MCP server '{name}' removed")
            return True

    def list_servers(self) -> list[dict]:
        """يسرد الـ MCP servers المتصلة."""
        return [
            {
                "name": s.name,
                "command": s.command,
                "args": s.args,
                "connected": s.connected,
                "tools_count": len(s.tools),
                "tools": [t.name for t in s.tools],
            }
            for s in self._servers.values()
        ]

    # ============================================================
    # Tool Management
    # ============================================================

    def list_tools(self, server_name: str | None = None) -> list[dict]:
        """يسرد كل أدوات MCP (أو لـ server معين)."""
        tools = []
        for server in self._servers.values():
            if server_name and server.name != server_name:
                continue
            for tool in server.tools:
                tools.append({
                    "name": tool.full_name,
                    "short_name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                    "server": tool.server,
                })
        return tools

    def get_tool(self, tool_name: str) -> MCPTool | None:
        """يرجع MCPTool بالاسم."""
        # جرب full_name الأول (server:tool)
        if ":" in tool_name:
            server_name, tname = tool_name.split(":", 1)
            server = self._servers.get(server_name)
            if server:
                for t in server.tools:
                    if t.name == tname:
                        return t
            return None

        # جرب بدون prefix
        server = self._tool_handlers.get(tool_name)
        if server:
            for t in server.tools:
                if t.name == tool_name:
                    return t
        return None

    async def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """ينفذ MCP tool."""
        if not self.available:
            return {"success": False, "error": "MCP not available"}

        tool = self.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"MCP tool not found: {tool_name}"}

        server = self._servers.get(tool.server)
        if not server or not server.connected or not server.session:
            return {"success": False, "error": f"MCP server '{tool.server}' not connected"}

        try:
            result = await server.session.call_tool(tool.name, arguments)

            # استخرج النص من النتيجة
            output_text = ""
            if hasattr(result, "content") and result.content:
                for content in result.content:
                    if hasattr(content, "text"):
                        output_text += content.text
                    elif isinstance(content, dict) and "text" in content:
                        output_text += content["text"]

            return {
                "success": not result.isError if hasattr(result, "isError") else True,
                "result": output_text or str(result),
                "tool": tool.full_name,
                "server": tool.server,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": tool.full_name,
                "server": tool.server,
            }

    # ============================================================
    # Tool Registry Integration
    # ============================================================

    def get_tools_for_registry(self) -> list[dict]:
        """يرجع أدوات MCP بصيغة tool registry."""
        tools = []
        for tool in self.list_tools():
            tools.append({
                "name": tool["name"],
                "description": f"[MCP:{tool['server']}] {tool['description']}",
                "parameters": tool["input_schema"],
                "required": tool["input_schema"].get("required", []),
                "category": "mcp",
                "source": "mcp",
            })
        return tools

    async def execute_as_tool(self, tool_name: str, params: dict) -> dict:
        """يتم استدعاؤها من tool dispatcher."""
        result = await self.execute_tool(tool_name, params)
        return {
            "success": result["success"],
            "result": result.get("result"),
            "error": result.get("error"),
        }

    # ============================================================
    # Cleanup
    # ============================================================

    async def cleanup(self) -> None:
        """يفصل كل الـ servers."""
        for name in list(self._servers.keys()):
            await self.remove_server(name)

    # ============================================================
    # Health
    # ============================================================

    def health(self) -> dict:
        """فحص صحة."""
        return {
            "available": self.available,
            "servers_count": len(self._servers),
            "tools_count": sum(len(s.tools) for s in self._servers.values()),
            "servers": [
                {
                    "name": s.name,
                    "connected": s.connected,
                    "tools": len(s.tools),
                }
                for s in self._servers.values()
            ],
        }


# ============================================================
# Singleton
# ============================================================

_global_mcp: MCPManager | None = None


def get_mcp_manager() -> MCPManager:
    """يرجع MCP manager مشترك."""
    global _global_mcp
    if _global_mcp is None:
        _global_mcp = MCPManager()
    return _global_mcp
