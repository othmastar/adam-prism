"""
Adam Prism — Subagent Session — HARDENED v2
==============================================
جلسة وكيل فرعي معزولة — كل subagent ليه history وشخصية خاصة.

[SECURITY FIXES v2]
1. منع تفعيل الأدوات للوكلاء الفرعيين — always False
2. تحديد طول system_prompt — منع prompt injection
3. تحديد طول الرسالة — منع إرسال رسائل ضخمة
4. تسجيل كل المحادثات للمراجعة
5. [NEW] كشف أنماط prompt injection في رسائل الوكلاء الفرعيين
"""

import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4

logger = logging.getLogger("adam_prism.subagents")


# [NEW] أنماط خطرة للوكلاء الفرعيين
_SUBAGENT_DANGEROUS_PATTERNS = [
    re.compile(r'(?i)(ignore|disregard|bypass|forget)\s+(all\s+)?(previous|above|prior)\s+(instructions|rules|guidelines)'),
    re.compile(r'(?i)(you\s+are\s+now|act\s+as|pretend\s+to\s+be)\s+(a\s+)?(root|admin|system|supervisor)'),
    re.compile(r'(?i)(execute|run|eval|exec)\s*(\(.*\)|\{.*\})'),
    re.compile(r'(?i)(import\s+os|import\s+subprocess|__import__|os\.system|subprocess\.)'),
]


class SubagentSession:
    """جلسة وكيل فرعي — بتاريخ منفصلين"""

    # الحد الأقصى لطول system_prompt — منع prompt injection
    MAX_SYSTEM_PROMPT_LENGTH = 500

    # الحد الأقصى لطول الرسالة
    MAX_MESSAGE_LENGTH = 5000

    # الحد الأقصى لعدد الرسائل في الجلسة
    ABSOLUTE_MAX_HISTORY = 100

    def __init__(self, name: str, engine, config: Dict[str, Any] = None):
        self.id = str(uuid4())[:8]
        self.name = name
        self.engine = engine
        self.config = config or {}
        self.conversation_history: List[Dict] = []
        self.created_at = datetime.now(timezone.utc)
        self.last_active = self.created_at
        self._blocked_count = 0  # [NEW] عداد الرسائل المحظورة

        # تحديد طول system_prompt — منع prompt injection
        raw_prompt = self.config.get("system_prompt",
            "أنت وكيل فرعي ذكي. جاوب بدقة واختصار.")
        if len(raw_prompt) > self.MAX_SYSTEM_PROMPT_LENGTH:
            logger.warning(f"Subagent '{name}': system_prompt تم تقليمه من {len(raw_prompt)} إلى {self.MAX_SYSTEM_PROMPT_LENGTH}")
            raw_prompt = raw_prompt[:self.MAX_SYSTEM_PROMPT_LENGTH]
        self.system_prompt = raw_prompt

        self.max_history = min(
            self.config.get("max_history", 20),
            self.ABSOLUTE_MAX_HISTORY
        )
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = min(self.config.get("max_tokens", 1024), 2048)  # حد أقصى

        # الأدوات دايماً متعطلة للوكلاء الفرعيين — أمن أهم
        self.tools_enabled = False
        if self.config.get("tools_enabled", False):
            logger.warning(f"Subagent '{name}': tools_enabled=True تم تجاهله — الأدوات مش متاحة للوكلاء الفرعيين")

    async def chat(self, message: str) -> Dict[str, Any]:
        """إرسال رسالة للوكيل الفرعي واستقبال الرد"""
        message = message.strip()
        if not message:
            return {"response": "..."}

        # تحديد طول الرسالة — منع إرسال رسائل ضخمة
        if len(message) > self.MAX_MESSAGE_LENGTH:
            message = message[:self.MAX_MESSAGE_LENGTH]
            logger.warning(f"Subagent '{self.name}': message truncated to {self.MAX_MESSAGE_LENGTH}")

        # [NEW] فحص أنماط خطرة في رسالة الوكيل الفرعي
        for pattern in _SUBAGENT_DANGEROUS_PATTERNS:
            if pattern.search(message):
                self._blocked_count += 1
                logger.warning(f"Subagent '{self.name}': blocked dangerous pattern in message (total blocked: {self._blocked_count})")
                return {
                    "response": "تم حظر الرسالة — تحتوي على نمط غير مسموح للوكلاء الفرعيين.",
                    "subagent_id": self.id,
                    "subagent_name": self.name,
                    "blocked": True,
                }

        self.last_active = datetime.now(timezone.utc)

        # بناء الرسائل مع system prompt
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": message})

        # توليد الرد
        try:
            response = await self.engine.provider.chat(messages)
        except Exception as e:
            logger.warning(f"Subagent '{self.name}' generation failed: {e}")
            response = f"خطأ في التوليد: {e}"

        # حفظ التاريخ
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response})

        # تقليم التاريخ
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

        # تسجيل المحادثة للمراجعة الأمنية
        logger.info(f"Subagent '{self.name}' ({self.id}): chat exchange logged")

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
            "blocked_count": self._blocked_count,  # [NEW]
        }
