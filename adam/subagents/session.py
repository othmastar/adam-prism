"""
Adam Prism — Subagent Session
==============================
جلسة وكيل فرعي معزولة — كل subagent ليه history وشخصية خاصة.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4

logger = logging.getLogger("adam_prism.subagents")


class SubagentSession:
    """جلسة وكيل فرعي — بي和历史 منفصلين"""

    def __init__(self, name: str, engine, config: Dict[str, Any] = None):
        self.id = str(uuid4())[:8]
        self.name = name
        self.engine = engine
        self.config = config or {}
        self.conversation_history: List[Dict] = []
        self.created_at = datetime.now(timezone.utc)
        self.last_active = self.created_at
        self.system_prompt = self.config.get("system_prompt",
            "أنت وكيل فرعي ذكي. جاوب بدقة واختصار.")
        self.max_history = self.config.get("max_history", 20)
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 1024)
        self.tools_enabled = self.config.get("tools_enabled", False)

    async def chat(self, message: str) -> Dict[str, Any]:
        """إرسال رسالة للوكيل الفرعي واستقبال الرد"""
        message = message.strip()
        if not message:
            return {"response": "..."}

        self.last_active = datetime.now(timezone.utc)

        # بناء الرسائل مع system prompt
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": message})

        # توليد الرد
        try:
            response = await self.engine.provider.chat(messages)
        except Exception as e:
            logger.warning(f"⚠️ Subagent '{self.name}' generation failed: {e}")
            response = f"⚠️ خطأ في التوليد: {e}"

        # حفظ التاريخ
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response})

        # تقليم التاريخ
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

        return {
            "response": response,
            "subagent_id": self.id,
            "subagent_name": self.name,
            "created_at": self.created_at.isoformat(),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "messages_count": len(self.conversation_history),
            "system_prompt": self.system_prompt[:100] if self.system_prompt else "",
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools_enabled": self.tools_enabled,
        }
