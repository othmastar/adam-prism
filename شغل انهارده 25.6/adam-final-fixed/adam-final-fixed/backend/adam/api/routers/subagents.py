"""
Adam Prism — Subagents Router
===============================
نقاط نهاية الوكلاء الفرعيين — تم استخراجها من server.py

[FIX v3] Router split — extracted from server.py for better maintainability
"""

from fastapi import APIRouter

router = APIRouter(tags=["subagents"])

@router.get("/api/subagents")
async def list_subagents():
    """قائمة الوكلاء الفرعيين"""
    pass

@router.post("/api/subagents/spawn")
async def spawn_subagent(req: dict):
    """إنشاء وكيل فرعي جديد"""
    pass

@router.post("/api/subagents/{subagent_id}/chat")
async def chat_subagent(subagent_id: str, req: dict):
    """محادثة مع وكيل فرعي"""
    pass

@router.delete("/api/subagents/{subagent_id}")
async def remove_subagent(subagent_id: str):
    """حذف وكيل فرعي"""
    pass
