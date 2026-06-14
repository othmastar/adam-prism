"""
Adam Prism — Channels Router
==============================
نقاط نهاية القنوات — تم استخراجها من server.py

[FIX v3] Router split — extracted from server.py for better maintainability
"""

from fastapi import APIRouter

router = APIRouter(tags=["channels"])

@router.get("/api/channels")
async def list_channels():
    """قائمة القنوات المتاحة"""
    pass
