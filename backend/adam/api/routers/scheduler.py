"""
Adam Prism — Scheduler Router
===============================
نقاط نهاية الجدولة — تم استخراجها من server.py

[FIX v3] Router split — extracted from server.py for better maintainability
"""

from fastapi import APIRouter

router = APIRouter(tags=["scheduler"])

@router.get("/api/scheduler/jobs")
async def list_scheduled_jobs():
    """قائمة المهام المجدولة"""
    pass

@router.post("/api/scheduler/interval")
async def add_interval_job(req: dict):
    """إضافة مهمة دورية"""
    pass

@router.post("/api/scheduler/once")
async def add_once_job(req: dict):
    """إضافة مهمة لمرة واحدة"""
    pass

@router.delete("/api/scheduler/jobs/{job_id}")
async def remove_scheduled_job(job_id: str):
    """حذف مهمة مجدولة"""
    pass
