"""
Adam Prism — Scheduler
========================
جدولة المهام: cron, interval, مرة واحدة.
لتشغيل تقارير، ريماندات، أدوات، backup في الخلفية.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Awaitable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

logger = logging.getLogger("adam_prism.scheduler")

JobFunc = Callable[..., Awaitable[Any]]


class AdamScheduler:
    """جدولة مهام آدم — تعمل في خلفية المحرك"""

    def __init__(self, engine=None):
        self.engine = engine
        self.scheduler = AsyncIOScheduler()
        self._jobs: Dict[str, Dict] = {}
        self._running = False

    def _safe_next_run(self, job_id: str) -> str:
        """Get next_run_time safely — pending jobs don't have this attr"""
        try:
            job = self.scheduler.get_job(job_id)
            if job is None:
                return ""
            return str(job.next_run_time)
        except AttributeError:
            return ""

    def _ensure_running(self):
        if not self._running:
            try:
                self.scheduler.start()
                self._running = True
                logger.info("✅ Scheduler started")
            except RuntimeError as e:
                if "event loop" in str(e).lower():
                    logger.debug("Scheduler مش started — لسه في sync context، هيبدأ أول استدعاء")

    def start(self):
        self._ensure_running()

    def stop(self):
        if self._running:
            self.scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Scheduler stopped")

    def add_cron(self, job_id: str, cron_expr: str, func: JobFunc,
                 args: List = None, kwargs: Dict = None, name: str = ""):
        """إضافة مهمة cron"""
        self._ensure_running()
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            raise ValueError("cron_expr لازم يكون 5 أجزاء: دقيقة ساعة يوم شهر أسبوع")
        trigger = CronTrigger(
            minute=parts[0], hour=parts[1], day=parts[2],
            month=parts[3], day_of_week=parts[4]
        )
        self.scheduler.add_job(
            func, trigger, args=args or [], kwargs=kwargs or {},
            id=job_id, replace_existing=True,
            name=name or job_id,
            misfire_grace_time=300
        )
        self._jobs[job_id] = {
            "type": "cron", "expr": cron_expr, "name": name or job_id,
            "next_run": self._safe_next_run(job_id) or ""
        }
        logger.info(f"📅 Cron '{job_id}' added: {cron_expr}")

    def add_interval(self, job_id: str, seconds: int, func: JobFunc,
                     args: List = None, kwargs: Dict = None, name: str = ""):
        """إضافة مهمة دورية"""
        self._ensure_running()
        trigger = IntervalTrigger(seconds=seconds)
        self.scheduler.add_job(
            func, trigger, args=args or [], kwargs=kwargs or {},
            id=job_id, replace_existing=True,
            name=name or job_id
        )
        self._jobs[job_id] = {
            "type": "interval", "seconds": seconds, "name": name or job_id,
            "next_run": self._safe_next_run(job_id)
        }
        logger.info(f"⏱ Interval '{job_id}' added: every {seconds}s")

    def add_once(self, job_id: str, run_at: datetime, func: JobFunc,
                 args: List = None, kwargs: Dict = None, name: str = ""):
        """إضافة مهمة مرة واحدة"""
        self._ensure_running()
        trigger = DateTrigger(run_date=run_at)
        self.scheduler.add_job(
            func, trigger, args=args or [], kwargs=kwargs or {},
            id=job_id, replace_existing=True,
            name=name or job_id
        )
        self._jobs[job_id] = {
            "type": "once", "run_at": run_at.isoformat(), "name": name or job_id,
            "next_run": self._safe_next_run(job_id)
        }
        logger.info(f"⏰ One-time '{job_id}': {run_at.isoformat()}")

    def remove(self, job_id: str) -> bool:
        if job_id in self._jobs:
            self.scheduler.remove_job(job_id)
            del self._jobs[job_id]
            logger.info(f"🗑 Job '{job_id}' removed")
            return True
        return False

    def list_jobs(self) -> List[Dict]:
        jobs = []
        for job_id, info in self._jobs.items():
            jobs.append({
                "id": job_id,
                "name": info["name"],
                "type": info["type"],
                "schedule": info.get("expr") or info.get("seconds") or info.get("run_at"),
                "next_run": self._safe_next_run(job_id),
            })
        return jobs

    def get_job(self, job_id: str) -> Optional[Dict]:
        info = self._jobs.get(job_id)
        if not info:
            return None
        return {
            "id": job_id,
            "name": info["name"],
            "type": info["type"],
            "details": info,
            "next_run": self._safe_next_run(job_id),
        }
