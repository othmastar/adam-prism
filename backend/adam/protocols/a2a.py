"""
Adam Prism — A2A (Agent-to-Agent) Protocol Support
=====================================================
دعم بروتوكول Google A2A للتواصل بين الوكلاء.

Google A2A (Agent-to-Agent) protocol implementation for inter-agent
communication. Supports agent discovery via Agent Card, task-based
messaging, and FastAPI endpoint integration.

بروتوكول A2A / A2A Protocol:
  - AgentCard: بطاقة الوكيل — Agent discovery card
  - A2AMessage: رسالة بين وكلاء — Inter-agent message
  - A2AServer: خادم A2A — A2A server with task management
  - FastAPI router: نقاط نهاية A2A — A2A endpoints

نقاط النهاية / Endpoints:
  - GET  /.well-known/agent.json   → بطاقة الوكيل — Agent card
  - POST /a2a/task                 → استقبال مهمة — Receive task
  - GET  /a2a/task/{task_id}       → حالة المهمة — Task status
  - DELETE /a2a/task/{task_id}     → إلغاء المهمة — Cancel task
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("adam_prism.protocols.a2a")


# ═══════════════════════════════════════════════════════════════
# أنماط البيانات / Data Models
# ═══════════════════════════════════════════════════════════════

@dataclass
class AgentCard:
    """
    بطاقة الوكيل — Agent discovery card (A2A protocol).

    بطاقة تعريفية للوكيل تُنشر في /.well-known/agent.json
    لتمكين اكتشاف الوكلاء الآخرين.

    Attributes / الخصائص:
        name: اسم الوكيل — Agent name
        description: وصف الوكيل — Agent description
        url: عنوان URL للوكيل — Agent URL
        capabilities: قدرات الوكيل — Agent capabilities
        version: إصدار البروتوكول — Protocol version
    """
    name: str = "Adam Prism"
    description: str = "Digital Twin AI Framework — إطار الذكاء الاصطناعي التوأم الرقمي"
    url: str = "http://localhost:8000"
    capabilities: List[str] = field(default_factory=lambda: [
        "chat", "code_generation", "research", "analysis",
        "tool_execution", "workflow", "voice", "memory",
    ])
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس — Convert to dict."""
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "capabilities": self.capabilities,
            "version": self.version,
            "protocol": "a2a",
        }


@dataclass
class A2AMessage:
    """
    رسالة A2A — An A2A protocol message.

    Attributes / الخصائص:
        task_id: معرف المهمة — Task ID
        sender: المرسل — Sender agent name
        receiver: المستقبل — Receiver agent name
        content: محتوى الرسالة — Message content
        artifacts: المرفقات — Artifacts (files, data, etc.)
        timestamp: وقت الإرسال — Send timestamp
        message_type: نوع الرسالة — Message type
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str = ""
    content: Any = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    message_type: str = "task"

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس — Convert to dict."""
        return {
            "task_id": self.task_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "artifacts": self.artifacts,
            "timestamp": self.timestamp,
            "message_type": self.message_type,
        }


# ═══════════════════════════════════════════════════════════════
# Pydantic Models for API
# ═══════════════════════════════════════════════════════════════

class A2ATaskRequest(BaseModel):
    """
    طلب مهمة A2A — A2A task request body.
    """
    task_id: Optional[str] = Field(None, description="معرف المهمة — Task ID (auto-generated if not provided)")
    sender: str = Field(..., description="المرسل — Sender agent name")
    receiver: str = Field("adam_prism", description="المستقبل — Receiver agent name")
    content: Any = Field(..., description="محتوى المهمة — Task content")
    artifacts: list = Field(default_factory=list, description="المرفقات — Artifacts")
    message_type: str = Field("task", description="نوع الرسالة — Message type")


# ═══════════════════════════════════════════════════════════════
# A2A Server
# ═══════════════════════════════════════════════════════════════

class A2AServer:
    """
    خادم A2A — Agent-to-Agent server.

    يدير بطاقة الوكيل والمهام الواردة والصادرة.
    Manages the agent card, incoming tasks, and outgoing communication.

    الاستخدام / Usage:
        server = A2AServer(
            agent_card=AgentCard(name="Adam Prism"),
            engine=my_engine,
        )
        # إضافة المسار إلى FastAPI — Add router to FastAPI
        app.include_router(server.create_router())
    """

    def __init__(
        self,
        agent_card: Optional[AgentCard] = None,
        engine: Any = None,
        max_tasks: int = 1000,
    ) -> None:
        """
        تهيئة خادم A2A — Initialize the A2A server.

        Args / المعاملات:
            agent_card: بطاقة الوكيل — Agent card
            engine: مرجع المحرك — Engine reference
            max_tasks: الحد الأقصى للمهام المحفوظة — Max stored tasks
        """
        self.agent_card = agent_card or AgentCard()
        self.engine = engine
        self._max_tasks = max_tasks

        # المهام الواردة — Incoming tasks
        self._tasks: Dict[str, Dict[str, Any]] = {}

        # عميل HTTP — HTTP client for outgoing messages
        self._http_client: Optional[httpx.AsyncClient] = None

        # قفل — Lock
        self._lock = asyncio.Lock()

    # ─────────────────────────────────────────────
    # بطاقة الوكيل / Agent Card
    # ─────────────────────────────────────────────

    def get_agent_card(self) -> AgentCard:
        """
        الحصول على بطاقة الوكيل — Get the agent card.
        """
        return self.agent_card

    # ─────────────────────────────────────────────
    # إرسال المهمة / Send Task
    # ─────────────────────────────────────────────

    async def send_task(
        self,
        target_url: str,
        message: A2AMessage,
        timeout: float = 30.0,
    ) -> A2AMessage:
        """
        إرسال مهمة إلى وكيل آخر — Send a task to another agent.

        Args / المعاملات:
            target_url: عنوان URL للوكيل المستهدف — Target agent URL
            message: الرسالة — The A2A message
            timeout: مهلة الانتظار — Request timeout

        Returns / المخرجات:
            رد الوكيل المستهدف — Response from target agent

        Raises / الاستثناءات:
            RuntimeError: إذا تعذر الإرسال — If sending fails
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=timeout)

        # إرسال إلى نقطة /a2a/task — Send to /a2a/task endpoint
        endpoint = f"{target_url.rstrip('/')}/a2a/task"

        try:
            response = await self._http_client.post(
                endpoint,
                json=message.to_dict(),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()
            return A2AMessage(
                task_id=result.get("task_id", message.task_id),
                sender=result.get("receiver", target_url),
                receiver=message.sender,
                content=result.get("content"),
                artifacts=result.get("artifacts", []),
                message_type="response",
            )

        except httpx.HTTPStatusError as exc:
            logger.error("A2A send failed (HTTP %d): %s", exc.response.status_code, exc)
            raise RuntimeError(f"A2A send failed: HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error("A2A send failed (network): %s", exc)
            raise RuntimeError(f"A2A send failed: {exc}") from exc

    # ─────────────────────────────────────────────
    # استقبال المهمة / Receive Task
    # ─────────────────────────────────────────────

    async def receive_task(self, message: A2AMessage) -> A2AMessage:
        """
        استقبال مهمة من وكيل آخر — Receive a task from another agent.

        Args / المعاملات:
            message: الرسالة الواردة — Incoming message

        Returns / المخرجات:
            رد على المهمة — Task response
        """
        task_id = message.task_id

        # حفظ المهمة — Store the task
        async with self._lock:
            self._tasks[task_id] = {
                "message": message.to_dict(),
                "status": "received",
                "received_at": time.time(),
                "result": None,
            }

            # تنظيف المهام القديمة — Cleanup old tasks
            if len(self._tasks) > self._max_tasks:
                oldest = sorted(
                    self._tasks.keys(),
                    key=lambda t: self._tasks[t]["received_at"],
                )
                for tid in oldest[: len(self._tasks) - self._max_tasks]:
                    del self._tasks[tid]

        logger.info(
            "A2A task received: %s from %s",
            task_id[:8], message.sender,
        )

        # معالجة المهمة — Process the task
        result_content = await self._process_task(message)

        # تحديث المهمة — Update task
        async with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = "completed"
                self._tasks[task_id]["result"] = result_content

        return A2AMessage(
            task_id=task_id,
            sender=self.agent_card.name,
            receiver=message.sender,
            content=result_content,
            message_type="response",
        )

    async def _process_task(self, message: A2AMessage) -> Any:
        """
        معالجة مهمة واردة — Process an incoming task.

        Args / المعاملات:
            message: الرسالة — Incoming message

        Returns / المخرجات:
            نتيجة المعالجة — Processing result
        """
        # إذا وُجد المحرك، وجّه الطلب — If engine exists, route the request
        if self.engine is not None:
            try:
                if hasattr(self.engine, "orchestrator") or hasattr(self.engine, "master"):
                    master = getattr(self.engine, "orchestrator", None) or getattr(self.engine, "master", None)
                    from adam.orchestrator.master import RequestType

                    # تحديد نوع الطلب — Determine request type
                    content_str = str(message.content) if message.content else ""
                    req_type = RequestType.CHAT  # افتراضي — Default

                    # محاولة تحديد النوع — Try to identify type
                    content_lower = content_str.lower()
                    if any(kw in content_lower for kw in ["code", "برمج", "كود"]):
                        req_type = RequestType.CODE_GENERATION
                    elif any(kw in content_lower for kw in ["research", "بحث", "search"]):
                        req_type = RequestType.RESEARCH
                    elif any(kw in content_lower for kw in ["analyz", "تحليل"]):
                        req_type = RequestType.ANALYSIS
                    elif any(kw in content_lower for kw in ["tool", "أداة", "execute"]):
                        req_type = RequestType.TOOL_EXECUTION

                    result = await master.route_request(req_type, {"message": content_str})
                    return result

                # محرك بدون منسق — Engine without orchestrator
                if hasattr(self.engine, "chat"):
                    return await self.engine.chat(message.content)

            except Exception as exc:
                logger.error("A2A task processing failed: %s", exc, exc_info=True)
                return {"error": str(exc), "status": "failed"}

        return {"status": "received", "content": message.content}

    # ─────────────────────────────────────────────
    # إدارة المهام / Task Management
    # ─────────────────────────────────────────────

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        الحصول على حالة مهمة — Get task status.

        Args / المعاملات:
            task_id: معرف المهمة — Task ID

        Returns / المخرجات:
            حالة المهمة — Task status dict

        Raises / الاستثناءات:
            KeyError: إذا لم تُوجَد المهمة — If task not found
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(f"Task {task_id} not found")
            return {
                "task_id": task_id,
                "status": task["status"],
                "received_at": task["received_at"],
                "result": task["result"],
                "sender": task["message"].get("sender", ""),
            }

    async def cancel_task(self, task_id: str) -> bool:
        """
        إلغاء مهمة — Cancel a task.

        Args / المعاملات:
            task_id: معرف المهمة — Task ID

        Returns / المخرجات:
            True إذا تم الإلغاء — True if cancelled
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return False
            if task["status"] in ("received", "processing"):
                task["status"] = "cancelled"
                return True
            return False

    # ─────────────────────────────────────────────
    # إنشاء مسار FastAPI / Create Router
    # ─────────────────────────────────────────────

    def create_router(self) -> APIRouter:
        """
        إنشاء مسار FastAPI لنقاط نهاية A2A — Create FastAPI router for A2A endpoints.

        Returns / المخرجات:
            مسار FastAPI — FastAPI APIRouter
        """
        router = APIRouter(tags=["a2a"])
        server = self  # إغلاق المرجع — Closure reference

        @router.get(
            "/.well-known/agent.json",
            summary="بطاقة الوكيل — Agent Card",
            description="يعيد بطاقة اكتشاف الوكيل وفقاً لبروتوكول A2A.",
        )
        async def get_agent_card() -> Dict[str, Any]:
            """بطاقة الوكيل — Agent discovery card."""
            return server.get_agent_card().to_dict()

        @router.post(
            "/a2a/task",
            summary="استقبال مهمة — Receive A2A task",
            description="يستقبل مهمة من وكيل آخر ويعيد الرد.",
        )
        async def receive_task(request: A2ATaskRequest) -> Dict[str, Any]:
            """استقبال مهمة — Receive a task from another agent."""
            message = A2AMessage(
                task_id=request.task_id or str(uuid.uuid4()),
                sender=request.sender,
                receiver=request.receiver,
                content=request.content,
                artifacts=request.artifacts,
                message_type=request.message_type,
            )

            try:
                response = await server.receive_task(message)
                return response.to_dict()
            except Exception as exc:
                logger.error("A2A task receive failed: %s", exc, exc_info=True)
                raise HTTPException(status_code=500, detail=str(exc))

        @router.get(
            "/a2a/task/{task_id}",
            summary="حالة المهمة — Task status",
            description="يعيد حالة مهمة A2A محددة.",
        )
        async def get_task_status(task_id: str) -> Dict[str, Any]:
            """حالة المهمة — Get task status."""
            try:
                return await server.get_task_status(task_id)
            except KeyError:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        @router.delete(
            "/a2a/task/{task_id}",
            summary="إلغاء المهمة — Cancel task",
            description="يلغي مهمة A2A قيد التنفيذ.",
        )
        async def cancel_task(task_id: str) -> Dict[str, Any]:
            """إلغاء المهمة — Cancel a task."""
            cancelled = await server.cancel_task(task_id)
            if not cancelled:
                raise HTTPException(
                    status_code=404,
                    detail=f"Task {task_id} not found or cannot be cancelled",
                )
            return {"task_id": task_id, "status": "cancelled"}

        return router

    # ─────────────────────────────────────────────
    # الإيقاف / Shutdown
    # ─────────────────────────────────────────────

    async def close(self) -> None:
        """
        إغلاق خادم A2A — Close the A2A server and HTTP client.
        """
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        logger.info("A2A server closed")
