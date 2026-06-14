"""
Adam Prism — Telegram Channel Adapter — HARDENED v2
======================================================
Long-polling عبر Telegram Bot API.

[M20 FIX]
- Create a persistent httpx.AsyncClient in __init__ and reuse it
  instead of creating a new client per message
"""

import logging
from typing import Any

from .base import BaseChannel

logger = logging.getLogger("adam_prism.channels.telegram")

class TelegramChannel(BaseChannel):
    name = "telegram"
    requires = ["bot_token"]
    is_polling = True
    is_webhook = False

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.bot_token = cfg.get("bot_token", config.get("telegram_bot_token", ""))
        self.authorized_chat_ids = cfg.get("authorized_chat_ids", config.get("authorized_chat_ids", []))
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_update_id = 0
        # [M20] Persistent HTTP client — reused for all requests
        import httpx
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self):
        """[M20] Get or create the persistent HTTP client."""
        import httpx
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client

    async def start_polling(self):
        if not self.bot_token:
            logger.warning("لا يوجد Bot Token للتليجرام")
            return
        self.running = True
        logger.info("📡 Telegram polling active")
        client = await self._get_client()  # [M20] Reuse persistent client
        while self.running:
            try:
                resp = await client.get(
                    f"{self.api_base}/getUpdates",
                    params={"offset": self.last_update_id + 1, "timeout": 30},
                )
                for update in resp.json().get("result", []):
                    self.last_update_id = update.get("update_id", 0)
                    await self._process(update)
            except Exception:
                logger.exception("Telegram polling error:")
                import asyncio
                await asyncio.sleep(5)

    async def _process(self, update: dict):
        msg = update.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        if not chat_id:
            return
        if self.authorized_chat_ids and chat_id not in self.authorized_chat_ids:
            await self.send_message(str(chat_id), "⛔ غير مصرح بالوصول.")
            return
        if "text" in msg:
            await self._handle_text(str(chat_id), msg["text"])

    async def _handle_text(self, chat_id: str, text: str):
        if self.engine:
            result = await self.engine.chat(text)
            await self.send_message(chat_id, result.get("response", ""))
        else:
            await self.send_message(chat_id, "المحرك غير متصل.")

    async def send_message(self, target: str, text: str, parse_mode: str = "Markdown"):
        if not self.bot_token:
            return
        # [M20] Reuse persistent client instead of creating a new one per message
        client = await self._get_client()
        try:
            for chunk in [text[i:i+4096] for i in range(0, len(text), 4096)]:
                await client.post(
                    f"{self.api_base}/sendMessage",
                    json={"chat_id": int(target), "text": chunk, "parse_mode": parse_mode},
                )
        except Exception:
            logger.exception("Telegram send failed:")

    async def close(self):
        """[M20] Properly close the persistent HTTP client."""
        if self._http_client is not None and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    def stop(self):
        self.running = False
