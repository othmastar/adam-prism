"""
Adam Prism — API Routers Package
===================================
ملفات التوجيه المنفصلة — كل ملف يتعامل مع مجموعة واحدة من نقاط النهاية

[FIX v3] تم تقسيم server.py (1334 سطر) إلى ملفات منفصلة لتحسين الصيانة
"""

from adam.api.routers.chat import router as chat_router
from adam.api.routers.knowledge import router as knowledge_router
from adam.api.routers.memory import router as memory_router
from adam.api.routers.tools import router as tools_router
from adam.api.routers.skills import router as skills_router
from adam.api.routers.subagents import router as subagents_router
from adam.api.routers.voice import router as voice_router
from adam.api.routers.mcp import router as mcp_router
from adam.api.routers.engine import router as engine_router
from adam.api.routers.channels import router as channels_router
from adam.api.routers.plugins import router as plugins_router
from adam.api.routers.scheduler import router as scheduler_router
from adam.api.routers.permissions import router as permissions_router

__all__ = [
    "chat_router",
    "knowledge_router",
    "memory_router",
    "tools_router",
    "skills_router",
    "subagents_router",
    "voice_router",
    "mcp_router",
    "engine_router",
    "channels_router",
    "plugins_router",
    "scheduler_router",
    "permissions_router",
]
