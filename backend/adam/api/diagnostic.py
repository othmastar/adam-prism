"""
Adam Prism — Diagnostic API Router
====================================
مسار API للتشخيص ولوحة المعلومات والمراقبة.

FastAPI router providing diagnostic endpoints for system health,
event bus stats, task queue stats, smart routing, and workflow execution.

نقاط النهاية / Endpoints:
  - GET  /api/orchestrator/diagnostic     → تشخيص شامل — Full diagnostics
  - GET  /api/orchestrator/dashboard       → بيانات لوحة المعلومات — Dashboard data
  - GET  /api/orchestrator/health/{module} → صحة موديول — Module health
  - GET  /api/orchestrator/events/stats    → إحصائيات ناقل الأحداث — Event bus stats
  - GET  /api/orchestrator/tasks/stats     → إحصائيات طابور المهام — Task queue stats
  - POST /api/orchestrator/route           → توجيه ذكي — Smart route a request
  - POST /api/orchestrator/workflow        → تنفيذ سير عمل — Execute a workflow
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("adam_prism.api.diagnostic")


# ═══════════════════════════════════════════════════════════════
# نماذج الطلب/الاستجابة / Request/Response Models
# ═══════════════════════════════════════════════════════════════

class RouteRequest(BaseModel):
    """
    طلب توجيه — Smart routing request.
    """
    request_type: str = Field(
        ...,
        description="نوع الطلب — Request type (CHAT, CODE_GENERATION, RESEARCH, ANALYSIS, TOOL_EXECUTION, WORKFLOW, SYSTEM)",
        examples=["CHAT"],
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="بيانات الطلب — Request data",
    )


class WorkflowRequest(BaseModel):
    """
    طلب سير عمل — Workflow execution request.
    """
    name: str = Field(
        ...,
        description="اسم سير العمل — Workflow name",
        examples=["research_and_summarize"],
    )
    steps: list = Field(
        ...,
        description="خطوات سير العمل — Workflow steps",
        examples=[[{"name": "search", "module": "memory", "action": "search"}]],
    )
    stop_on_failure: bool = Field(
        default=True,
        description="إيقاف عند الفشل — Stop on first failure",
    )


class DiagnosticResponse(BaseModel):
    """
    استجابة التشخيص — Diagnostic response.
    """
    status: str = "ok"
    data: Dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
# Router Creation
# ═══════════════════════════════════════════════════════════════

def create_diagnostic_router(engine: Any = None) -> APIRouter:
    """
    إنشاء مسار التشخيص — Create the diagnostic API router.

    Args / المعاملات:
        engine: مرجع المحرك الرئيسي — Reference to the main engine

    Returns / المخرجات:
        مسار FastAPI — FastAPI APIRouter
    """
    router = APIRouter(
        prefix="/api/orchestrator",
        tags=["orchestrator", "diagnostics"],
    )

    def _get_master() -> Any:
        """
        الحصول على المنسق من المحرك — Get MasterOrchestrator from engine.
        """
        if engine is None:
            raise HTTPException(status_code=503, detail="Engine not available")
        master = getattr(engine, "orchestrator", None) or getattr(engine, "master", None)
        if master is None:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        return master

    # ─────────────────────────────────────────────
    # تشخيص شامل / Full Diagnostics
    # ─────────────────────────────────────────────

    @router.get(
        "/diagnostic",
        response_model=DiagnosticResponse,
        summary="تشخيص شامل للنظام — Full system diagnostic",
        description="يعيد تشخيصاً شاملاً يشمل صحة الموديولات وناقل الأحداث وطابور المهام.",
    )
    async def get_diagnostic() -> DiagnosticResponse:
        """
        تشخيص شامل — Get comprehensive system diagnostics.
        """
        try:
            master = _get_master()
            diagnostics = await master.get_diagnostics()
            return DiagnosticResponse(status="ok", data=diagnostics)
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Diagnostic failed: %s", exc, exc_info=True)
            return DiagnosticResponse(
                status="error",
                data={"error": str(exc)},
            )

    # ─────────────────────────────────────────────
    # لوحة المعلومات / Dashboard
    # ─────────────────────────────────────────────

    @router.get(
        "/dashboard",
        summary="بيانات لوحة المعلومات — Dashboard data",
        description="بيانات مختصرة للوحة المعلومات تشمل صحة النظام والإحصائيات.",
    )
    async def get_dashboard() -> Dict[str, Any]:
        """
        بيانات لوحة المعلومات — Get dashboard summary data.
        """
        try:
            master = _get_master()
            health = await master.check_health()
            event_stats = await master.event_bus.get_stats()
            task_stats = await master.task_queue.get_stats()

            return {
                "status": "healthy" if health.get("overall_healthy") else "degraded",
                "health": {
                    "overall": health.get("overall_healthy", False),
                    "modules": {
                        name: info["healthy"]
                        for name, info in health.get("modules", {}).items()
                    },
                },
                "events": {
                    "published": event_stats.get("total_published", 0),
                    "delivered": event_stats.get("total_delivered", 0),
                    "failed": event_stats.get("total_failed", 0),
                    "subscribers": event_stats.get("subscriber_count", 0),
                },
                "tasks": {
                    "pending": task_stats.get("pending", 0),
                    "running": task_stats.get("running", 0),
                    "completed": task_stats.get("completed", 0),
                    "failed": task_stats.get("failed", 0),
                },
                "circuit_breakers": {
                    name: info.get("open", False)
                    for name, info in (await master.get_diagnostics()).get("master_orchestrator", {}).get("circuit_breakers", {}).items()
                },
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Dashboard failed: %s", exc, exc_info=True)
            return {"status": "error", "error": str(exc)}

    # ─────────────────────────────────────────────
    # صحة موديول / Module Health
    # ─────────────────────────────────────────────

    @router.get(
        "/health/{module_name}",
        summary="صحة موديول محدد — Module health check",
        description="يعيد حالة صحة موديول محدد.",
    )
    async def get_module_health(module_name: str) -> Dict[str, Any]:
        """
        صحة موديول محدد — Get health for a specific module.
        """
        try:
            master = _get_master()
            health = await master.get_module_health(module_name)
            return {
                "module": health.name,
                "healthy": health.healthy,
                "latency_ms": health.latency_ms,
                "failure_count": health.failure_count,
                "last_check": health.last_check,
                "circuit_open": master._is_circuit_open(module_name),
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Module health check failed for '%s': %s", module_name, exc)
            raise HTTPException(status_code=500, detail=str(exc))

    # ─────────────────────────────────────────────
    # إحصائيات ناقل الأحداث / Event Bus Stats
    # ─────────────────────────────────────────────

    @router.get(
        "/events/stats",
        summary="إحصائيات ناقل الأحداث — Event bus statistics",
        description="يعيد إحصائيات ناقل الأحداث.",
    )
    async def get_event_stats() -> Dict[str, Any]:
        """
        إحصائيات ناقل الأحداث — Get event bus statistics.
        """
        try:
            master = _get_master()
            return await master.event_bus.get_stats()
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Event stats failed: %s", exc)
            return {"error": str(exc)}

    # ─────────────────────────────────────────────
    # إحصائيات طابور المهام / Task Queue Stats
    # ─────────────────────────────────────────────

    @router.get(
        "/tasks/stats",
        summary="إحصائيات طابور المهام — Task queue statistics",
        description="يعيد إحصائيات طابور المهام.",
    )
    async def get_task_stats() -> Dict[str, Any]:
        """
        إحصائيات طابور المهام — Get task queue statistics.
        """
        try:
            master = _get_master()
            return await master.task_queue.get_stats()
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Task stats failed: %s", exc)
            return {"error": str(exc)}

    # ─────────────────────────────────────────────
    # توجيه ذكي / Smart Route
    # ─────────────────────────────────────────────

    @router.post(
        "/route",
        summary="توجيه ذكي للطلب — Smart route a request",
        description="يوجه الطلب إلى الموديول الأنسب بناءً على النوع والأنماط المتعلمة.",
    )
    async def smart_route(request: RouteRequest) -> Dict[str, Any]:
        """
        توجيه ذكي — Smart route a request to the best module.
        """
        try:
            master = _get_master()
            from adam.orchestrator.master import RequestType

            # تحويل نوع الطلب — Parse request type
            try:
                req_type = RequestType(request.request_type.upper())
            except ValueError:
                valid = [rt.value for rt in RequestType]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid request_type '{request.request_type}'. Valid: {valid}",
                )

            result = await master.route_request(req_type, request.data)
            return result

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Smart route failed: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    # ─────────────────────────────────────────────
    # تنفيذ سير عمل / Execute Workflow
    # ─────────────────────────────────────────────

    @router.post(
        "/workflow",
        summary="تنفيذ سير عمل — Execute a workflow",
        description="ينفذ سير عمل متعدد الخطوات مع إمكانية التدهور البديل.",
    )
    async def execute_workflow(request: WorkflowRequest) -> Dict[str, Any]:
        """
        تنفيذ سير عمل — Execute a multi-step workflow.
        """
        try:
            master = _get_master()

            workflow_def = {
                "name": request.name,
                "steps": request.steps,
                "stop_on_failure": request.stop_on_failure,
            }

            result = await master.execute_workflow(workflow_def)
            return result

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Workflow execution failed: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))

    return router
