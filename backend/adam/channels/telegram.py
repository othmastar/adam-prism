"""
Adam Prism — Telegram Channel Adapter
======================================
Long-polling عبر Telegram Bot API.
"""

import logging
from typing import Dict, Any
from .base import BaseChannel

logger = logging.getLogger("adam_prism.channels.telegram")


class TelegramChannel(BaseChannel):
    name = "telegram"
    requires = ["bot_token"]
    is_polling = True
    is_webhook = False

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.bot_token = cfg.get("bot_token", config.get("telegram_bot_token", ""))
        self.authorized_chat_ids = cfg.get("authorized_chat_ids", config.get("authorized_chat_ids", []))
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_update_id = 0

    async def start_polling(self):
        if not self.bot_token:
            logger.warning("لا يوجد Bot Token للتليجرام")
            return
        self.running = True
        logger.info("📡 Telegram polling active")
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            while self.running:
                try:
                    resp = await client.get(
                        f"{self.api_base}/getUpdates",
                        params={"offset": self.last_update_id + 1, "timeout": 30},
                    )
                    for update in resp.json().get("result", []):
                        self.last_update_id = update.get("update_id", 0)
                        await self._process(update)
                except Exception as e:
                    logger.error(f"Telegram polling error: {e}")
                    import asyncio
                    await asyncio.sleep(5)

    async def _process(self, update: Dict):
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
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                for chunk in [text[i:i+4096] for i in range(0, len(text), 4096)]:
                    await client.post(
                        f"{self.api_base}/sendMessage",
                        json={"chat_id": int(target), "text": chunk, "parse_mode": parse_mode},
                    )
            except Exception as e:
                logger.error(f"Telegram send failed: {e}")

    def stop(self):
        self.running = False
