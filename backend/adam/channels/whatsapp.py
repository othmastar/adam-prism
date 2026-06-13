"""
Adam Prism — WhatsApp Channel Adapter
======================================
WhatsApp Business API عبر webhooks (Meta Cloud API).
"""

import json
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional
from .base import BaseChannel

logger = logging.getLogger("adam_prism.channels.whatsapp")


class WhatsAppChannel(BaseChannel):
    name = "whatsapp"
    requires = ["phone_number_id", "access_token"]
    is_polling = False
    is_webhook = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.phone_number_id = cfg.get("phone_number_id", config.get("whatsapp_phone_number_id", ""))
        self.access_token = cfg.get("access_token", config.get("whatsapp_access_token", ""))
        self.webhook_verify_token = cfg.get("webhook_verify_token", config.get("whatsapp_webhook_verify_token", ""))
        if not self.webhook_verify_token:
            logger.warning("WhatsApp webhook_verify_token is not configured! Webhook verification will fail. "
                           "Set 'webhook_verify_token' in config or WHATSAPP_WEBHOOK_VERIFY_TOKEN env var.")
        self.app_secret = cfg.get("app_secret", config.get("whatsapp_app_secret", ""))
        self.api_version = cfg.get("api_version", config.get("whatsapp_api_version", "v22.0"))
        self.api_base = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"

    async def start_polling(self):
        self.running = True
        logger.info("📡 WhatsApp webhook mode (endpoints at /webhook/whatsapp)")

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        if mode == "subscribe" and token == self.webhook_verify_token:
            return challenge
        return None

    def verify_signature(self, raw_body: bytes, signature_header: str) -> bool:
        if not self.app_secret:
            logger.warning("WhatsApp: app_secret غير مضبوط — توثيق webhook معطل")
            return False
        expected = hmac.new(self.app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature_header)

    async def process_incoming(self, payload: Dict) -> Dict:
        results = []
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    results.append(await self._handle_message(msg, value.get("metadata", {})))
        return {"status": "processed", "count": len(results)}

    async def _handle_message(self, msg: Dict, metadata: Dict) -> Dict:
        from_number = msg.get("from", "")
        msg_type = msg.get("type", "text")
        if msg_type == "text":
            text = msg.get("text", {}).get("body", "")
            if self.engine:
                result = await self.engine.chat(text)
                await self.send_message(from_number, result.get("response", ""))
                return {"from": from_number, "response": "sent"}
        return {"from": from_number, "status": "unhandled"}

    async def send_message(self, target: str, text: str, preview_url: bool = False):
        if not self.access_token:
            logger.warning("No WhatsApp access token")
            return
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                await client.post(
                    f"{self.api_base}/messages",
                    headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
                    json={"messaging_product": "whatsapp", "to": target, "type": "text",
                          "text": {"preview_url": preview_url, "body": text}},
                )
            except Exception as e:
                logger.error(f"WhatsApp send failed: {e}")

    def stop(self):
        self.running = False

    def get_webhook_routes(self) -> list:
        return [
            {"path": "/webhook/whatsapp", "method": "GET", "handler": self._webhook_get},
            {"path": "/webhook/whatsapp", "method": "POST", "handler": self._webhook_post},
        ]

    async def _webhook_get(self, request) -> dict:
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        result = self.verify_webhook(mode, token, challenge)
        if result:
            return {"content": result, "status_code": 200}
        return {"content": "Forbidden", "status_code": 403}

    async def _webhook_post(self, request) -> dict:
        raw_body = await request.body()
        sig = request.headers.get("X-Hub-Signature-256", "")
        if not self.verify_signature(raw_body, sig):
            return {"content": "Invalid signature", "status_code": 403}
        payload = json.loads(raw_body)
        await self.process_incoming(payload)
        return {"content": "OK", "status_code": 200}
