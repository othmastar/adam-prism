"""
Adam Prism — Context Compressor
================================
يحل مشكلة "أنا آدم" + قطع السياق.

يدخل في engine/chat.py قبل _generate().
- يحافظ على آخر 8 رسائل verbatim
- يلخص الباقي بـ auxiliary model (qwen2.5:0.5b)
- يحافظ على system prompt كامل
- fallback deterministic لو الـ LLM فشل

Integration:
    from adam.enhancements.context_compressor import ContextCompressor
    compressor = ContextCompressor(
        auxiliary_client=aux_client,
        max_context_tokens=8192,
        reserve_for_response=2048,
    )
    messages, stats = await compressor.compress(messages)
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any

import httpx

logger = logging.getLogger("adam_prism.compressor")

# ============================================================
# Constants
# ============================================================

CHARS_PER_TOKEN = 4

SUMMARY_PREFIX = (
    "[CONTEXT COMPACTION — REFERENCE ONLY] "
    "ملخص للمحادثة السابقة. تعامل معه كمرجع. "
    "رد فقط على آخر رسالة من المستخدم. "
    "لا تكمل مهام ذكرت في الملخص إلا لو طلب المستخدم صراحة."
)
END_MARKER = "--- نهاية الملخص ---"


def estimate_tokens(text: str) -> int:
    """تقدير عدد الـ tokens من نص."""
    if not text:
        return 0
    arabic_ratio = sum(1 for c in text if "\u0600" <= c <= "\u06FF") / max(len(text), 1)
    effective = len(text) * (1 + arabic_ratio * 0.5)
    return max(1, int(effective // CHARS_PER_TOKEN))


def estimate_messages_tokens(messages: list[dict]) -> int:
    """تقدير إجمالي الـ tokens في قائمة رسائل."""
    total = 0
    for msg in messages:
        total += 4  # overhead per message
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") in ("image_url", "image"):
                        total += 1600
                    else:
                        total += estimate_tokens(part.get("text", ""))
    return total


# ============================================================
# Context Compressor
# ============================================================

class ContextCompressor:
    """ضاغط السياق — يحافظ على آخر N رسائل + يلخص الباقي."""

    def __init__(
        self,
        auxiliary_client=None,
        ollama_url: str = "http://localhost:11434",
        auxiliary_model: str = "qwen2.5:0.5b",
        max_context_tokens: int = 8192,
        reserve_for_response: int = 2048,
        compression_threshold: float = 0.75,
        protect_last_n: int = 8,
        timeout: float = 30.0,
    ):
        self.aux = auxiliary_client
        self.ollama_url = ollama_url.rstrip("/")
        self.auxiliary_model = auxiliary_model
        self.usable = max_context_tokens - reserve_for_response
        self.threshold = compression_threshold
        self.protect_last_n = protect_last_n
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._available: bool | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=3, max_keepalive_connections=2),
            )
        return self._client

    def should_compress(self, messages: list[dict]) -> bool:
        return estimate_messages_tokens(messages) > self.usable * self.threshold

    async def compress(self, messages: list[dict]) -> tuple[list[dict], dict]:
        """يضغط الرسائل. يرجع (compressed_messages, stats)."""
        original_tokens = estimate_messages_tokens(messages)

        if not self.should_compress(messages):
            return messages, {"compressed": False, "tokens": original_tokens}

        # فصل system messages (مهمة — فيها "أنت آدم")
        system_messages = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        protect_count = min(self.protect_last_n, len(non_system))
        if protect_count >= len(non_system):
            return messages, {"compressed": False, "tokens": original_tokens}

        to_keep = non_system[-protect_count:]
        to_compress = non_system[:-protect_count]

        if not to_compress:
            return messages, {"compressed": False, "tokens": original_tokens}

        # جرب LLM summarization
        summary = None
        method = "none"
        try:
            summary = await self._llm_summary(to_compress)
            method = "llm"
        except Exception as e:
            logger.warning(f"LLM summarization failed: {e}")
            summary = None

        if not summary:
            summary = self._fallback_summary(to_compress)
            method = "fallback"

        summary_msg = {
            "role": "system",
            "content": f"{SUMMARY_PREFIX}\n\n{summary}\n\n{END_MARKER}",
        }
        compressed = system_messages + [summary_msg] + to_keep
        compressed_tokens = estimate_messages_tokens(compressed)

        return compressed, {
            "compressed": True,
            "method": method,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "tokens_saved": original_tokens - compressed_tokens,
            "messages_protected": protect_count,
            "messages_compressed": len(to_compress),
        }

    async def _llm_summary(self, messages: list[dict]) -> str:
        """يلخص بـ auxiliary model."""
        conv_text = "\n\n".join(
            f"[{m['role']}]: {m.get('content', '')[:500]}"
            for m in messages
        )

        prompt = f"""لخّص المحادثة في نقاط مختصرة. ركّز على:
1. القرارات المهمة
2. الملفات والمسارات المذكورة
3. المهام المعلقة
4. معلومات المستخدم

المحادثة:
{conv_text[:5000]}

الملخص (نقاط مختصرة بالعربية):"""

        # لو فيه auxiliary_client، استخدمه
        if self.aux and hasattr(self.aux, "chat"):
            return await self.aux.chat(
                [
                    {"role": "system", "content": "أنت ملخّص محادثات. اكتب ملخص مختصر بالعربية."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.3,
            )

        # fallback مباشر لـ Ollama
        client = await self._get_client()
        response = await client.post(
            f"{self.ollama_url}/api/chat",
            json={
                "model": self.auxiliary_model,
                "messages": [
                    {"role": "system", "content": "أنت ملخّص محادثات. اكتب ملخص مختصر بالعربية."},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"num_predict": 500, "temperature": 0.3},
            },
        )
        if response.status_code != 200:
            if self._available is None:
                logger.warning(
                    f"Auxiliary model '{self.auxiliary_model}' not available. "
                    f"Run: ollama pull {self.auxiliary_model}"
                )
                self._available = False
            raise RuntimeError(f"Status {response.status_code}")
        self._available = True
        return response.json().get("message", {}).get("content", "").strip()

    def _fallback_summary(self, messages: list[dict]) -> str:
        """ملخص deterministic لو الـ LLM فشل."""
        if not messages:
            return "لا يوجد محتوى للتلخيص."

        user_msgs = []
        asst_msgs = []
        paths = set()

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if isinstance(content, str):
                # استخرج file paths
                for m in re.finditer(r"(?:/|~/?|[A-Za-z]:\\)[^\s`'\"<>]+", content):
                    paths.add(m.group().rstrip(".,:;"))
                if role == "user" and len(user_msgs) < 10:
                    user_msgs.append(content[:200])
                elif role == "assistant" and len(asst_msgs) < 10:
                    asst_msgs.append(content[:200])

        parts = []
        if user_msgs:
            parts.append("## رسائل المستخدم:\n" + "\n- ".join([""] + user_msgs))
        if asst_msgs:
            parts.append("## ردود المساعد:\n" + "\n- ".join([""] + asst_msgs))
        if paths:
            parts.append("## الملفات المذكورة:\n" + ", ".join(list(paths)[:10]))

        summary = "\n\n".join(parts)
        if len(summary) > 4000:
            summary = summary[:4000] + "\n... [مقتطع]"
        return summary

    async def cleanup(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
