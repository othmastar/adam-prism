"""
Adam Prism — Skills Router
============================
نقاط نهاية المهارات — تم استخراجها من server.py

[FIX v3] Router split — extracted from server.py for better maintainability
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["skills"])


@router.get("/api/skills")
async def list_skills():
    """عرض المهارات المتاحة"""
    pass


@router.get("/api/skills/list")
async def skills_list():
    """قائمة المهارات التفصيلية"""
    pass


@router.post("/api/skills/load")
async def skills_load(req: dict):
    """تحميل مهارة"""
    pass
