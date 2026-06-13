"""
Adam Prism — Diagnostic & Orchestrator API Endpoints
======================================================
نقاط تشخيص وتنسيق إضافية لـ API server.
يتم دمجها في server.py عبر include_router.

Features:
1. System diagnostic endpoint
2. Master Orchestrator dashboard
3. Event bus stats
4. Task queue management
5. Module health check
"""

import contextlib
import logging
from datetime import UTC

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger("adam_prism.api.diagnostic")

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


@router.get("/diagnostic")
async def run_diagnostic(request: Request):
    """تشخيص كامل للنظام — يفحص كل مكون ويقدم توصيات"""
    engine = request.app.state.engine if hasattr(request.app.state, "engine") else None
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not attached")

    diagnosis = {
        "timestamp": _now(),
        "overall_health": "unknown",
        "modules": {},
        "issues": [],
        "recommendations": [],
    }

    healthy_count = 0
    total_count = 0
    critical_modules = ["security_guard", "security", "provider", "knowledge"]

    module_list = [
        ("memory", engine.memory),
        ("ethics", engine.ethics),
        ("security", engine.security),
        ("notebook", engine.notebook),
        ("knowledge", engine.knowledge),
        ("eyes", engine.eyes),
        ("tools", engine.tools),
        ("pipeline", engine.pipeline),
        ("trace_recorder", engine.trace_recorder),
        ("scheduler", engine.scheduler),
        ("plugins", engine.plugins),
        ("subagents", engine.subagents),
        ("security_guard", engine.security_guard),
        ("continuous_learner", engine.continuous_learner),
    ]

    for name, module in module_list:
        total_count += 1
        is_healthy = module is not None
        is_stub = is_healthy and hasattr(module, '_methods')  # _Stub detection

        module_diag = {
            "attached": is_healthy,
            "is_stub": is_stub,
            "health": "healthy" if (is_healthy and not is_stub) else ("degraded" if is_stub else "offline"),
        }

        if is_healthy and not is_stub:
            healthy_count += 1
        elif is_stub:
            diagnosis["issues"].append(f"Module '{name}' is running as stub (degraded)")
        else:
            diagnosis["issues"].append(f"Module '{name}' is offline")

        if name in critical_modules and not is_healthy:
            diagnosis["recommendations"].append(f"CRITICAL: Initialize '{name}' module immediately")

        diagnosis["modules"][name] = module_diag

    # Overall health
    if total_count > 0:
        health_ratio = healthy_count / total_count
        if health_ratio >= 0.8:
            diagnosis["overall_health"] = "healthy"
        elif health_ratio >= 0.5:
            diagnosis["overall_health"] = "degraded"
        else:
            diagnosis["overall_health"] = "critical"

    # Provider health
    if engine.provider:
        try:
            provider_mode = engine.provider.mode
            diagnosis["provider"] = {
                "mode": provider_mode,
                "healthy": True,
            }
        except Exception as e:
            diagnosis["provider"] = {"healthy": False, "error": str(e)}

    # Metrics
    if engine.metrics:
        diagnosis["metrics"] = engine.metrics.dump()

    return diagnosis


@router.get("/dashboard")
async def orchestrator_dashboard(request: Request):
    """لوحة تحكم Master Orchestrator"""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        return {
            "status": "orchestrator_not_initialized",
            "message": "Master Orchestrator is not running. Start it to enable advanced coordination."
        }
    return orchestrator.get_dashboard()


@router.get("/health/{module_name}")
async def module_health(module_name: str, request: Request):
    """فحص صحة موديول محدد"""
    engine = request.app.state.engine if hasattr(request.app.state, "engine") else None
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not attached")

    module = getattr(engine, module_name, None)
    if module is None:
        return {"module": module_name, "health": "offline", "attached": False}

    is_stub = hasattr(module, '_methods')
    health_info = {
        "module": module_name,
        "attached": True,
        "is_stub": is_stub,
        "health": "degraded" if is_stub else "healthy",
    }

    # Get module-specific status if available
    if hasattr(module, 'get_status'):
        with contextlib.suppress(Exception):
            health_info["details"] = module.get_status()

    return health_info


@router.get("/events/stats")
async def event_bus_stats(request: Request):
    """إحصائيات ناقل الأحداث"""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        return {"status": "orchestrator_not_initialized"}
    return orchestrator.event_bus.stats()


@router.get("/tasks/stats")
async def task_queue_stats(request: Request):
    """إحصائيات طابور المهام"""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        return {"status": "orchestrator_not_initialized"}
    return orchestrator.task_queue.stats()


@router.get("/tasks/list")
async def task_list(request: Request, status: str | None = None, limit: int = 50):
    """قائمة المهام"""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        return {"status": "orchestrator_not_initialized"}
    return {"tasks": orchestrator.task_queue.list_tasks(status=status, limit=limit)}


@router.post("/route")
async def route_request(request: Request):
    """توجيه طلب عبر Master Orchestrator"""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    body = await request.json()
    message = body.get("message", "")
    context = body.get("context", {})

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    result = await orchestrator.route_request(message, context)
    return result


@router.post("/workflow")
async def execute_workflow(request: Request):
    """تنفيذ سير عمل عبر Master Orchestrator"""
    from adam.orchestrator.master import Workflow, WorkflowStep

    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    body = await request.json()
    name = body.get("name", "unnamed")
    steps_data = body.get("steps", [])

    steps = []
    for s in steps_data:
        steps.append(WorkflowStep(
            name=s.get("name", "step"),
            module=s.get("module", "engine"),
            action=s.get("action", ""),
            params=s.get("params", {}),
            depends_on=s.get("depends_on", []),
            timeout=s.get("timeout", 30.0),
        ))

    workflow = Workflow(name=name, steps=steps)
    result = await orchestrator.execute_workflow(workflow)
    return result


def _now():
    from datetime import datetime
    return datetime.now(UTC).isoformat()
