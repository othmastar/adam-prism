"""
Adam Prism — Integration Layer
================================
الجزء اللي بيربط كل المكونات ببعضها.

مش بناء من الصفر — ده "glue code" بيربط:
- engine/chat.py (الموجود عندك)
- memory/store.py + memory/system.py (الموجود عندك)
- eyes/browser.py (الموجود عندك)
- tools/mcp.py (الموجود عندك)

WITH الجديد:
- ContextCompressor ( enhancements/context_compressor.py)
- VectorMemory (enhancements/vector_embeddings.py)
- EnhancedBrowser (enhancements/enhanced_browser.py)
- MCPManager (enhancements/mcp_integration.py)

Integration points:
1. في engine/chat.py قبل _generate() → ContextCompressor
2. في memory/store.py search() → VectorMemory hybrid search
3. في eyes/browser.py → EnhancedBrowser multi-tab
4. في engine/tools/__init__.py → MCPManager tools

Usage in engine/base.py __init__:
    from adam.enhancements.integration import IntegrationLayer
    self.integration = IntegrationLayer(self.config)
    await self.integration.init()

Usage in engine/chat.py:
    messages = self._build_messages(...)
    messages, comp_stats = await self.integration.compress(messages)
    ltm_context = await self.integration.recall_memory(user_message)
    ...

Usage in engine/tools/__init__.py:
    if tool_name.startswith("mcp:"):
        return await self.integration.execute_mcp_tool(tool_name, params)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from adam.engine import ContextCompressor, AuxiliaryClient
from adam.memory import MemoryStore as VectorMemory
from .enhanced_browser import EnhancedBrowser
from .mcp_integration import MCPManager

logger = logging.getLogger("adam_prism.integration")


# ============================================================
# Integration Layer
# ============================================================

class IntegrationLayer:
    """يربط كل المكونات مع بعض."""

    def __init__(self, config: dict[str, Any]):
        self.config = config

        # استخرج الإعدادات
        ollama_url = config.get("ollama_base", "http://localhost:11434")
        lora_url = config.get("lora_server_url", "http://localhost:7861")
        auxiliary_model = config.get("auxiliary_model", "qwen2.5:0.5b")
        embedding_model = config.get("embedding_model", "nomic-embed-text")
        max_context = config.get("context_window", 8192)
        memory_db = config.get("vector_memory_db", "~/.adam/vector_memory.db")

        # 1. Context Compressor (with auxiliary model for LLM summarization)
        self._auxiliary: AuxiliaryClient | None = None
        try:
            self._auxiliary = AuxiliaryClient(ollama_url, auxiliary_model)
        except Exception:
            self._auxiliary = None
        self.compressor = ContextCompressor(
            auxiliary=self._auxiliary,
            max_context_tokens=max_context,
            reserve_for_response=config.get("reserve_for_response", 2048),
            compression_threshold=config.get("compression_threshold", 0.75),
            protect_last_n=config.get("protect_last_n", 8),
        )

        # 2. Vector Memory (LTM مع embeddings)
        self.vector_memory = VectorMemory(
            db_path=memory_db,
            ollama_url=ollama_url,
            embedding_model=embedding_model,
        )

        # 3. Enhanced Browser (Playwright multi-tab)
        self.browser = None  # lazy init
        browser_enabled = config.get("browser_enabled", True)
        if browser_enabled:
            self.browser = EnhancedBrowser(
                headless=config.get("browser_headless", True),
                browser_type=config.get("browser_type", "chromium"),
                max_pages=config.get("browser_max_pages", 5),
            )

        # 4. MCP Manager
        self.mcp = MCPManager(
            max_servers=config.get("mcp_max_servers", 10),
        )

        self._initialized = False

    async def init(self) -> None:
        """يهيّئ كل المكونات async."""
        if self._initialized:
            return

        # Init browser
        if self.browser:
            try:
                ok = await self.browser.init()
                if ok:
                    logger.info("✅ EnhancedBrowser initialized")
                else:
                    logger.warning("⚠️ EnhancedBrowser failed, falling back to existing eyes/browser.py")
                    self.browser = None
            except Exception as e:
                logger.warning(f"Browser init failed: {e}")
                self.browser = None

        # Init MCP
        try:
            ok = await self.mcp.init()
            if ok:
                logger.info("✅ MCP Manager initialized")
            else:
                logger.warning("⚠️ MCP library not installed — install with: pip install mcp")
        except Exception as e:
            logger.warning(f"MCP init failed: {e}")

        self._initialized = True
        logger.info("IntegrationLayer ready")

    # ============================================================
    # 1. Context Compression (يُستخدم في engine/chat.py)
    # ============================================================

    async def compress_context(self, messages: list[dict]) -> tuple[list[dict], dict]:
        """يضغط السياق. يُستخدم قبل _generate() في chat.py."""
        return await self.compressor.compress(messages)

    # ============================================================
    # 2. Vector Memory (يُستخدم في engine/context.py + chat.py)
    # ============================================================

    async def store_memory(
        self, content: str, type: str = "semantic",
        priority: int = 3, tags: list[str] | None = None,
        session_id: str | None = None,
    ) -> int | None:
        """يخزّن ذكرى في الـ vector memory."""
        return await self.vector_memory.store(
            content=content, type=type, priority=priority,
            tags=tags, source="chat", session_id=session_id,
        )

    async def recall_memory(self, query: str, max_memories: int = 5) -> str:
        """يسترجع ذكريات للسياق. يُستخدم في _build_context()."""
        return await self.vector_memory.recall_for_context(
            query, max_memories=max_memories, max_chars=1500
        )

    async def search_memory(self, query: str, top_k: int = 5) -> list:
        """بحث في الذاكرة."""
        return await self.vector_memory.search(query, top_k=top_k)

    # ============================================================
    # 3. Enhanced Browser (يُستخدم في eyes/browser.py)
    # ============================================================

    async def browser_open(self, url: str) -> dict:
        """يفتح URL في متصفح multi-tab."""
        if not self.browser:
            return {"success": False, "error": "Browser not available"}
        try:
            page_id = await self.browser.open(url)
            return {"success": True, "page_id": page_id, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def browser_fetch(self, url: str) -> dict:
        """يجلب محتوى URL."""
        if not self.browser:
            return {"success": False, "error": "Browser not available"}
        try:
            page_id = await self.browser.open(url)
            text = await self.browser.get_text(page_id)
            await self.browser.close_page(page_id)
            return {"success": True, "content": text[:10000], "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def browser_screenshot(self, page_id: str, full_page: bool = False) -> dict:
        """يلتقط screenshot."""
        if not self.browser:
            return {"success": False, "error": "Browser not available"}
        return await self.browser.screenshot(page_id, full_page=full_page)

    def browser_list_pages(self) -> list[dict]:
        """يسرد الصفحات المفتوحة."""
        if not self.browser:
            return []
        return self.browser.list_pages()

    # ============================================================
    # 4. MCP Integration (يُستخدم في engine/tools/__init__.py)
    # ============================================================

    async def mcp_add_server(
        self, name: str, command: str, args: list[str], env: dict | None = None
    ) -> bool:
        """يضيف MCP server."""
        return await self.mcp.add_server(name, command, args, env)

    async def mcp_remove_server(self, name: str) -> bool:
        """يحذف MCP server."""
        return await self.mcp.remove_server(name)

    def mcp_list_servers(self) -> list[dict]:
        """يسرد MCP servers."""
        return self.mcp.list_servers()

    def mcp_list_tools(self) -> list[dict]:
        """يسرد MCP tools."""
        return self.mcp.list_tools()

    async def mcp_execute_tool(self, tool_name: str, params: dict) -> dict:
        """ينفذ MCP tool."""
        return await self.mcp.execute_tool(tool_name, params)

    # ============================================================
    # Health & Stats
    # ============================================================

    async def health_check(self) -> dict:
        """فحص صحة كل المكونات."""
        return {
            "compressor": True,  # synchronous, always available
            "vector_memory": await self.vector_memory.health_check(),
            "browser": await self.browser.health_check() if self.browser else False,
            "mcp": self.mcp.health(),
        }

    def stats(self) -> dict:
        """إحصائيات."""
        return {
            "vector_memory": self.vector_memory.stats(),
            "browser": self.browser.get_stats() if self.browser else {"available": False},
            "mcp": self.mcp.health(),
        }

    # ============================================================
    # Cleanup
    # ============================================================

    async def cleanup(self) -> None:
        """ينظف كل الموارد."""
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
        try:
            await self.mcp.cleanup()
        except Exception:
            pass
        try:
            await self.compressor.cleanup()
        except Exception:
            pass
        try:
            self.vector_memory.close()
        except Exception:
            pass


# ============================================================
# Factory
# ============================================================

_integration: IntegrationLayer | None = None


def get_integration(config: dict | None = None) -> IntegrationLayer:
    """يرجع IntegrationLayer مشترك."""
    global _integration
    if _integration is None:
        _integration = IntegrationLayer(config or {})
    return _integration


async def cleanup_integration() -> None:
    """ينظف الـ IntegrationLayer المشترك."""
    global _integration
    if _integration is not None:
        await _integration.cleanup()
        _integration = None
