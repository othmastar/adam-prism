"""
Adam Prism — Plugins Router
==============================
نقاط نهاية الإضافات — تم استخراجها من server.py

[FIX v3] Router split — extracted from server.py for better maintainability
"""

from fastapi import APIRouter

router = APIRouter(tags=["plugins"])


@router.get("/api/plugins")
async def list_plugins():
    """قائمة الإضافات"""
    pass


@router.post("/api/plugins/load")
async def load_plugin(req: dict):
    """تحميل إضافة من مسار"""
    pass


@router.delete("/api/plugins/{plugin_name}")
async def unload_plugin(plugin_name: str):
    """إلغاء تحميل إضافة"""
    pass
