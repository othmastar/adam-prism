"""
Adam Prism — Bulk Channel Adapters (15+ channels)
==================================================
تنفيذات أخف لكل القنوات التانية — كلها تتبع BaseChannel interface.
"""

import json
import logging
from typing import Dict, Any, Optional
from .base import BaseChannel

logger = logging.getLogger("adam_prism.channels.bulk")

BULK_CHANNELS: Dict[str, type] = {}


def _register(cls):
    BULK_CHANNELS[cls.name] = cls
    return cls


# ─── DISCORD ───────────────────────────────────────────────────────────
@_register
class DiscordChannel(BaseChannel):
    name = "discord"
    requires = ["bot_token"]
    is_polling = True
    is_webhook = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.bot_token = cfg.get("bot_token", "")
        self.api_base = "https://discord.com/api/v10"
        self._gateway_url = None
        self._session_id = None
        self._seq = 0

    async def start_polling(self):
        if not self.bot_token:
            return
        self.running = True
        logger.info("📡 Discord gateway polling active")
        await self._connect_gateway()

    async def _connect_gateway(self):
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.api_base}/gateway/bot", headers=self._headers())
            self._gateway_url = resp.json().get("url", "wss://gateway.discord.gg")
        import websockets
        uri = f"{self._gateway_url}/?v=10&encoding=json"
        async for ws in websockets.connect(uri):
            try:
                async for msg in ws:
                    data = json.loads(msg)
                    self._seq = data.get("s", self._seq)
                    if data["op"] == 10:
                        import asyncio
                        heartbeat_interval = data["d"]["heartbeat_interval"] / 1000
                        asyncio.create_task(self._heartbeat(ws, heartbeat_interval))
                        await ws.send(json.dumps({"op": 2, "d": {"token": self.bot_token, "intents": 512, "properties": {"os": "linux", "browser": "adam", "device": "adam"}}}))
                    elif data["op"] == 0:
                        await self._handle_dispatch(data)
                    elif data["op"] == 11:
                        pass
            except Exception as e:
                logger.error(f"Discord WS error: {e}")
                if not self.running:
                    break
                import asyncio
                await asyncio.sleep(5)

    async def _heartbeat(self, ws, interval):
        import asyncio
        while self.running:
            await asyncio.sleep(interval)
            try:
                await ws.send(json.dumps({"op": 1, "d": self._seq}))
            except Exception:
                break

    def _headers(self):
        return {"Authorization": f"Bot {self.bot_token}", "Content-Type": "application/json"}

    async def _handle_dispatch(self, data):
        t = data.get("t")
        d = data.get("d", {})
        if t == "READY":
            self._session_id = d["session_id"]
            logger.info(f"Discord ready as {d['user']['username']}")
        elif t == "MESSAGE_CREATE":
            if d.get("author", {}).get("bot"):
                return
            content = d.get("content", "")
            channel_id = d.get("channel_id")
            if content.startswith("!"):
                text = content[1:]
                if self.engine:
                    result = await self.engine.chat(text)
                    await self.send_message(channel_id, result.get("response", ""))

    async def send_message(self, target: str, text: str):
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                for chunk in self._chunk(text, 2000):
                    await client.post(f"{self.api_base}/channels/{target}/messages", headers=self._headers(),
                                      json={"content": chunk})
            except Exception as e:
                logger.error(f"Discord send failed: {e}")

    def _chunk(self, text: str, size: int):
        return [text[i:i+size] for i in range(0, len(text), size)]

    def get_webhook_routes(self) -> list:
        return [{"path": "/webhook/discord", "method": "POST", "handler": self._webhook_post}]

    async def _webhook_post(self, request) -> dict:
        data = await request.json()
        content = data.get("content", "")
        channel_id = data.get("channel_id", "")
        if content and channel_id and self.engine:
            result = await self.engine.chat(content)
            await self.send_message(channel_id, result.get("response", ""))
        return {"content": "OK", "status_code": 200}


# ─── SLACK ─────────────────────────────────────────────────────────────
@_register
class SlackChannel(BaseChannel):
    name = "slack"
    requires = ["bot_token"]
    is_polling = False
    is_webhook = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.bot_token = cfg.get("bot_token", "")
        self.signing_secret = cfg.get("signing_secret", "")
        self.api_base = "https://slack.com/api"

    async def start_polling(self):
        self.running = True
        logger.info("📡 Slack webhook mode (endpoints at /webhook/slack)")

    async def send_message(self, target: str, text: str):
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                await client.post(f"{self.api_base}/chat.postMessage",
                                  headers={"Authorization": f"Bearer {self.bot_token}", "Content-Type": "application/json"},
                                  json={"channel": target, "text": text})
            except Exception as e:
                logger.error(f"Slack send failed: {e}")

    def verify_signature(self, body: bytes, timestamp: str, signature: str) -> bool:
        if not self.signing_secret:
            logger.warning("Slack: signing_secret غير مضبوط — توثيق webhook معطل")
            return False
        import hashlib, hmac
        base = f"v0:{timestamp}:{body.decode()}"
        expected = "v0=" + hmac.new(self.signing_secret.encode(), base.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def get_webhook_routes(self) -> list:
        return [{"path": "/webhook/slack", "method": "POST", "handler": self._webhook_post}]

    async def _webhook_post(self, request) -> dict:
        body = await request.body()
        ts = request.headers.get("X-Slack-Request-Timestamp", "")
        sig = request.headers.get("X-Slack-Signature", "")
        if not self.verify_signature(body, ts, sig):
            return {"content": "Invalid signature", "status_code": 403}
        data = json.loads(body)
        if data.get("type") == "url_verification":
            return {"content": data.get("challenge", ""), "status_code": 200}
        if "event" in data:
            event = data["event"]
            if event.get("type") == "message" and "subtype" not in event:
                text = event.get("text", "")
                channel = event.get("channel", "")
                if text and channel and self.engine:
                    result = await self.engine.chat(text)
                    await self.send_message(channel, result.get("response", ""))
        return {"content": "OK", "status_code": 200}


# ─── EMAIL ─────────────────────────────────────────────────────────────
@_register
class EmailChannel(BaseChannel):
    name = "email"
    requires = ["smtp_host", "smtp_user", "smtp_pass"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.smtp_host = cfg.get("smtp_host", "")
        self.smtp_port = cfg.get("smtp_port", 587)
        self.smtp_user = cfg.get("smtp_user", "")
        self.smtp_pass = cfg.get("smtp_pass", "")
        self.imap_host = cfg.get("imap_host", "")
        self.imap_user = cfg.get("imap_user", cfg.get("smtp_user", ""))
        self.imap_pass = cfg.get("imap_pass", cfg.get("smtp_pass", ""))
        self.from_addr = cfg.get("from_addr", self.smtp_user)
        self._seen_ids = set()

    async def start_polling(self):
        if not self.imap_host:
            self.running = True
            logger.info("📡 Email ready (outgoing only, no IMAP configured)")
            return
        self.running = True
        logger.info(f"📡 Email polling {self.imap_host}")
        import asyncio
        while self.running:
            try:
                await self._check_inbox()
            except Exception as e:
                logger.error(f"Email poll error: {e}")
            await asyncio.sleep(60)

    async def _check_inbox(self):
        import imaplib, email as eml
        import asyncio
        loop = asyncio.get_event_loop()
        def _fetch():
            mail = imaplib.IMAP4_SSL(self.imap_host)
            mail.login(self.imap_user, self.imap_pass)
            mail.select("INBOX")
            _, data = mail.search(None, "UNSEEN")
            results = []
            for num in data[0].split() if data[0] else []:
                _, msg_data = mail.fetch(num, "(RFC822)")
                raw = msg_data[0][1]
                msg = eml.message_from_bytes(raw)
                subject = msg["Subject"] or ""
                from_addr = msg["From"] or ""
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="replace")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="replace")
                results.append({"from": from_addr, "subject": subject, "body": body})
            mail.logout()
            return results

        messages = await asyncio.get_event_loop().run_in_executor(None, _fetch)
        for msg in messages:
            if msg["body"] and self.engine and msg["from"] not in self._seen_ids:
                self._seen_ids.add(msg["from"])
                result = await self.engine.chat(msg["body"])
                await self.send_message(msg["from"], result.get("response", ""))

    async def send_message(self, target: str, text: str, subject: str = "آدم"):
        import smtplib
        from email.mime.text import MIMEText
        loop = asyncio.get_event_loop()
        def _send():
            msg = MIMEText(text, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = target
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as s:
                s.starttls()
                s.login(self.smtp_user, self.smtp_pass)
                s.send_message(msg)
        await loop.run_in_executor(None, _send)


# ─── SMS / TWILIO ──────────────────────────────────────────────────────
@_register
class SMSChannel(BaseChannel):
    name = "sms"
    requires = ["twilio_account_sid", "twilio_auth_token", "from_number"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.account_sid = cfg.get("twilio_account_sid", "")
        self.auth_token = cfg.get("twilio_auth_token", "")
        self.from_number = cfg.get("from_number", "")

    async def start_polling(self):
        self.running = True
        logger.info("📡 SMS ready (outgoing only via Twilio)")

    async def send_message(self, target: str, text: str):
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                    auth=(self.account_sid, self.auth_token),
                    data={"From": self.from_number, "To": target, "Body": text},
                )
            except Exception as e:
                logger.error(f"SMS send failed: {e}")

    def get_webhook_routes(self) -> list:
        return [{"path": "/webhook/sms", "method": "POST", "handler": self._webhook_post}]

    async def _webhook_post(self, request) -> dict:
        form = await request.form()
        sender = form.get("From", "")
        body = form.get("Body", "")
        if sender and body and self.engine:
            result = await self.engine.chat(body)
            await self.send_message(sender, result.get("response", ""))
        return {"content": "<Response></Response>", "status_code": 200, "media_type": "application/xml"}


# ─── WEBSOCKET SERVER ──────────────────────────────────────────────────
@_register
class WebSocketChannel(BaseChannel):
    name = "websocket"
    requires = []
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.host = cfg.get("host", "0.0.0.0")
        self.port = cfg.get("port", 8765)
        self._clients = set()

    async def start_polling(self):
        self.running = True
        import asyncio
        import websockets
        async def handler(ws):
            self._clients.add(ws)
            try:
                async for msg in ws:
                    if self.engine:
                        result = await self.engine.chat(msg)
                        await ws.send(json.dumps(result, ensure_ascii=False))
            finally:
                self._clients.discard(ws)
        async def serve():
            async with websockets.serve(handler, self.host, self.port):
                logger.info(f"📡 WebSocket server on ws://{self.host}:{self.port}")
                await asyncio.Future()
        self._task = asyncio.create_task(serve())

    async def send_message(self, target: str, text: str):
        for ws in list(self._clients):
            try:
                await ws.send(text)
            except Exception:
                self._clients.discard(ws)

    def stop(self):
        self.running = False
        if hasattr(self, "_task"):
            self._task.cancel()


# ─── WEB CHAT WIDGET ───────────────────────────────────────────────────
@_register
class WebChatChannel(BaseChannel):
    name = "webchat"
    requires = []
    is_polling = False
    is_webhook = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.allowed_origins = cfg.get("allowed_origins", ["*"])

    async def start_polling(self):
        self.running = True
        logger.info("📡 WebChat endpoints at /chat/webhook")

    async def send_message(self, target: str, text: str):
        pass

    def get_webhook_routes(self) -> list:
        return [
            {"path": "/chat/webhook", "method": "POST", "handler": self._webhook_post},
            {"path": "/chat/widget", "method": "GET", "handler": self._widget_get},
        ]

    async def _webhook_post(self, request) -> dict:
        data = await request.json()
        msg = data.get("message", "")
        session = data.get("session", "default")
        if msg and self.engine:
            result = await self.engine.chat(msg)
            return {"content": json.dumps({"response": result.get("response", ""), "session": session}, ensure_ascii=False), "status_code": 200}
        return {"content": json.dumps({"error": "empty message"}), "status_code": 400}

    async def _widget_get(self, request) -> dict:
        html = """<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><title>آدم</title>
<style>body{font-family:sans-serif;margin:0;background:#1a1a2e;color:#eee}.chat{max-width:600px;margin:auto;padding:20px}
#messages{height:400px;overflow-y:auto;border:1px solid #333;padding:10px;border-radius:8px;background:#16213e}
input{width:80%;padding:10px;border-radius:20px;border:1px solid #555;background:#0f3460;color:#eee}
button{padding:10px 20px;border-radius:20px;background:#e94560;color:#fff;border:none;cursor:pointer}
.user{color:#e94560;margin:5px 0}.bot{color:#53d769;margin:5px 0}</style></head><body>
<div class="chat"><h2>🤖 آدم</h2><div id="messages"></div>
<input id="msg" placeholder="اكتب رسالتك..."/><button onclick="send()">إرسال</button></div>
<script>
async function send(){const m=document.getElementById('msg');if(!m.value)return;
const d=document.getElementById('messages');d.innerHTML+='<div class="user">🧑 '+m.value+'</div>';
const r=await fetch('/chat/webhook',{method:'POST',body:JSON.stringify({message:m.value}),headers:{'Content-Type':'application/json'}});
const j=await r.json();d.innerHTML+='<div class="bot">🤖 '+j.response+'</div>';m.value='';d.scrollTop=d.scrollHeight;}
document.getElementById('msg').addEventListener('keydown',e=>{if(e.key==='Enter')send()});
</script></body></html>"""
        return {"content": html, "status_code": 200, "media_type": "text/html"}


# ─── TWITTER/X DM ──────────────────────────────────────────────────────
@_register
class TwitterChannel(BaseChannel):
    name = "twitter"
    requires = ["bearer_token"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.bearer_token = cfg.get("bearer_token", "")
        self.api_key = cfg.get("api_key", "")
        self.api_secret = cfg.get("api_secret", "")
        self._last_id = 0

    async def start_polling(self):
        if not self.bearer_token:
            return
        self.running = True
        logger.info("📡 Twitter DM polling active")
        import asyncio, httpx
        async with httpx.AsyncClient() as client:
            while self.running:
                try:
                    resp = await client.get(
                        "https://api.twitter.com/2/dm_events",
                        headers={"Authorization": f"Bearer {self.bearer_token}"},
                        params={"max_results": 5},
                    )
                    events = resp.json().get("data", [])
                    for ev in events:
                        eid = int(ev.get("id", 0))
                        if eid <= self._last_id:
                            continue
                        self._last_id = eid
                        sender = ev.get("sender_id", "")
                        text = ev.get("text", "")
                        if sender and text and self.engine:
                            result = await self.engine.chat(text)
                            await self.send_message(sender, result.get("response", ""))
                except Exception as e:
                    logger.error(f"Twitter poll error: {e}")
                await asyncio.sleep(30)

    async def send_message(self, target: str, text: str):
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    "https://api.twitter.com/2/dm_conversations",
                    headers={"Authorization": f"Bearer {self.bearer_token}", "Content-Type": "application/json"},
                    json={"conversation_type": "Personal", "participant_ids": [target],
                          "message": {"data": {"text": text}}})
            except Exception as e:
                logger.error(f"Twitter DM send failed: {e}")


# ─── FACEBOOK MESSENGER ────────────────────────────────────────────────
@_register
class FacebookChannel(BaseChannel):
    name = "facebook"
    requires = ["page_access_token"]
    is_polling = False
    is_webhook = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.page_access_token = cfg.get("page_access_token", "")
        self.app_secret = cfg.get("app_secret", "")
        self.api_base = "https://graph.facebook.com/v22.0/me"

    async def start_polling(self):
        self.running = True
        logger.info("📡 Facebook Messenger webhook at /webhook/facebook")

    async def send_message(self, target: str, text: str):
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.api_base}/messages",
                    params={"access_token": self.page_access_token},
                    json={"recipient": {"id": target}, "message": {"text": text}},
                )
            except Exception as e:
                logger.error(f"Facebook send failed: {e}")

    def verify_signature(self, body: bytes, signature: str) -> bool:
        if not self.app_secret:
            logger.warning("Facebook: app_secret غير مضبوط — توثيق webhook معطل")
            return False
        import hmac, hashlib
        expected = "sha256=" + hmac.new(self.app_secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def get_webhook_routes(self) -> list:
        return [
            {"path": "/webhook/facebook", "method": "GET", "handler": self._webhook_get},
            {"path": "/webhook/facebook", "method": "POST", "handler": self._webhook_post},
        ]

    async def _webhook_get(self, request) -> dict:
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        if mode == "subscribe" and token == self.app_secret:
            return {"content": challenge, "status_code": 200}
        return {"content": "Forbidden", "status_code": 403}

    async def _webhook_post(self, request) -> dict:
        raw = await request.body()
        sig = request.headers.get("X-Hub-Signature-256", "")
        if not self.verify_signature(raw, sig):
            return {"content": "Invalid sig", "status_code": 403}
        data = json.loads(raw)
        for entry in data.get("entry", []):
            for msg in entry.get("messaging", []):
                sender = msg.get("sender", {}).get("id", "")
                text = msg.get("message", {}).get("text", "")
                if sender and text and self.engine:
                    result = await self.engine.chat(text)
                    await self.send_message(sender, result.get("response", ""))
        return {"content": "OK", "status_code": 200}


# ─── MATRIX ────────────────────────────────────────────────────────────
@_register
class MatrixChannel(BaseChannel):
    name = "matrix"
    requires = ["homeserver", "access_token"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.homeserver = cfg.get("homeserver", "https://matrix.org")
        self.access_token = cfg.get("access_token", "")
        self.user_id = cfg.get("user_id", "")
        self._next_batch = ""

    async def start_polling(self):
        if not self.access_token:
            return
        self.running = True
        logger.info(f"📡 Matrix sync on {self.homeserver}")
        import asyncio, httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            while self.running:
                try:
                    resp = await client.get(
                        f"{self.homeserver}/_matrix/client/v3/sync",
                        headers={"Authorization": f"Bearer {self.access_token}"},
                        params={"since": self._next_batch} if self._next_batch else {},
                        timeout=30,
                    )
                    data = resp.json()
                    self._next_batch = data.get("next_batch", self._next_batch)
                    for room_id, room in data.get("rooms", {}).get("join", {}).items():
                        for ev in room.get("timeline", {}).get("events", []):
                            if ev.get("type") == "m.room.message" and ev.get("sender") != self.user_id:
                                body = ev.get("content", {}).get("body", "")
                                if body and self.engine:
                                    result = await self.engine.chat(body)
                                    await self._send_room(room_id, result.get("response", ""), client)
                except Exception as e:
                    logger.error(f"Matrix sync error: {e}")
                await asyncio.sleep(5)

    async def _send_room(self, room_id: str, text: str, client):
        try:
            await client.post(
                f"{self.homeserver}/_matrix/client/v3/rooms/{room_id}/send/m.room.message",
                headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
                json={"msgtype": "m.text", "body": text},
            )
        except Exception as e:
            logger.error(f"Matrix send failed: {e}")

    async def send_message(self, target: str, text: str):
        import httpx
        async with httpx.AsyncClient() as client:
            await self._send_room(target, text, client)


# ─── SIGNAL ────────────────────────────────────────────────────────────
@_register
class SignalChannel(BaseChannel):
    name = "signal"
    requires = ["cli_path"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.cli_path = cfg.get("cli_path", "signal-cli")
        self.number = cfg.get("number", "")

    async def start_polling(self):
        self.running = True
        logger.info("📡 Signal via CLI (receive via dbus or --receive)")
        import asyncio
        while self.running:
            try:
                proc = await asyncio.create_subprocess_exec(
                    self.cli_path, "-u", self.number, "receive",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                )
                stdout, _ = await proc.communicate()
                for line in stdout.decode(errors="replace").split("\n"):
                    if "Body:" in line and self.engine:
                        text = line.split("Body:", 1)[1].strip()
                        result = await self.engine.chat(text)
                        logger.info(f"Signal reply: {result.get('response', '')[:50]}...")
            except Exception as e:
                logger.error(f"Signal poll error: {e}")
            await asyncio.sleep(30)

    async def send_message(self, target: str, text: str):
        import asyncio
        try:
            proc = await asyncio.create_subprocess_exec(
                self.cli_path, "-u", self.number, "send", "-m", text, target,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
        except Exception as e:
            logger.error(f"Signal send failed: {e}")


# ══════════════════════════════════════════════════════════════════════
#  LIGHT ADAPTERS (13+) — implementations أبسط لكن same interface
# ══════════════════════════════════════════════════════════════════════

@_register
class InstagramChannel(BaseChannel):
    name = "instagram"
    requires = ["username", "password"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.username = cfg.get("username", "")
        self.password = cfg.get("password", "")

    async def start_polling(self):
        self.running = True
        logger.info("📡 Instagram channel (requires instagrapi or similar)")

    async def send_message(self, target: str, text: str):
        logger.info(f"Instagram DM to {target}: {text[:30]}...")

    def stop(self):
        self.running = False


@_register
class LINEChannel(BaseChannel):
    name = "line"
    requires = ["channel_access_token"]
    is_polling = False
    is_webhook = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.access_token = cfg.get("channel_access_token", "")

    async def start_polling(self):
        self.running = True
        logger.info("📡 LINE channel ready (webhook at /webhook/line)")

    async def send_message(self, target: str, text: str):
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    "https://api.line.me/v2/bot/message/push",
                    headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
                    json={"to": target, "messages": [{"type": "text", "text": text}]},
                )
            except Exception as e:
                logger.error(f"LINE send failed: {e}")

    def get_webhook_routes(self) -> list:
        return [{"path": "/webhook/line", "method": "POST", "handler": self._webhook_post}]

    async def _webhook_post(self, request) -> dict:
        data = await request.json()
        for ev in data.get("events", []):
            if ev.get("type") == "message" and ev.get("message", {}).get("type") == "text":
                reply_token = ev.get("replyToken", "")
                text = ev.get("message", {}).get("text", "")
                if text and self.engine:
                    result = await self.engine.chat(text)
                    import httpx
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            "https://api.line.me/v2/bot/message/reply",
                            headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
                            json={"replyToken": reply_token, "messages": [{"type": "text", "text": result.get("response", "")}]},
                        )
        return {"content": "OK", "status_code": 200}


@_register
class ViberChannel(BaseChannel):
    name = "viber"
    requires = ["auth_token"]
    is_polling = False
    is_webhook = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.auth_token = cfg.get("auth_token", "")

    async def start_polling(self):
        self.running = True
        logger.info("📡 Viber channel at /webhook/viber")

    async def send_message(self, target: str, text: str):
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    "https://chatapi.viber.com/pa/send_message",
                    headers={"X-Viber-Auth-Token": self.auth_token},
                    json={"receiver": target, "type": "text", "text": text},
                )
            except Exception as e:
                logger.error(f"Viber send failed: {e}")

    def get_webhook_routes(self) -> list:
        return [{"path": "/webhook/viber", "method": "POST", "handler": self._webhook_post}]

    async def _webhook_post(self, request) -> dict:
        data = await request.json()
        if data.get("event") == "message" and data.get("message", {}).get("type") == "text":
            sender = data.get("sender", {}).get("id", "")
            text = data.get("message", {}).get("text", "")
            if sender and text and self.engine:
                result = await self.engine.chat(text)
                await self.send_message(sender, result.get("response", ""))
        return {"content": "OK", "status_code": 200}


@_register
class TeamsChannel(BaseChannel):
    name = "teams"
    requires = ["webhook_url"]
    is_polling = False
    is_webhook = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.webhook_url = cfg.get("webhook_url", "")

    async def start_polling(self):
        self.running = True
        logger.info("📡 Teams channel (outgoing webhook)")

    async def send_message(self, target: str, text: str):
        url = target if target.startswith("http") else self.webhook_url
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json={"text": text})
            except Exception as e:
                logger.error(f"Teams send failed: {e}")

    def get_webhook_routes(self) -> list:
        return [{"path": "/webhook/teams", "method": "POST", "handler": self._webhook_post}]

    async def _webhook_post(self, request) -> dict:
        data = await request.json()
        text = data.get("text", "")
        if text and self.engine:
            result = await self.engine.chat(text)
            return {"content": json.dumps({"type": "message", "text": result.get("response", "")}), "status_code": 200}
        return {"content": "OK", "status_code": 200}


@_register
class GoogleChatChannel(BaseChannel):
    name = "googletalk"
    requires = ["webhook_url"]
    is_polling = False
    is_webhook = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.webhook_url = cfg.get("webhook_url", "")

    async def start_polling(self):
        self.running = True
        logger.info("📡 Google Chat channel (webhook)")

    async def send_message(self, target: str, text: str):
        url = target if target.startswith("http") else self.webhook_url
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                await client.post(url, json={"text": text})
            except Exception as e:
                logger.error(f"Google Chat send failed: {e}")

    def get_webhook_routes(self) -> list:
        return [{"path": "/webhook/googletalk", "method": "POST", "handler": self._webhook_post}]

    async def _webhook_post(self, request) -> dict:
        data = await request.json()
        text = data.get("text", data.get("message", {}).get("text", ""))
        if text and self.engine:
            result = await self.engine.chat(text)
            return {"content": json.dumps({"text": result.get("response", "")}), "status_code": 200}
        return {"content": "OK", "status_code": 200}


@_register
class IRCChannel(BaseChannel):
    name = "irc"
    requires = ["server", "nick"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.server = cfg.get("server", "irc.libera.chat")
        self.port = cfg.get("port", 6667)
        self.nick = cfg.get("nick", "adam-prism")
        self.channels_list = cfg.get("channels", ["#adam-prism"])

    async def start_polling(self):
        self.running = True
        logger.info(f"📡 IRC connecting to {self.server}")
        import asyncio
        reader, writer = await asyncio.open_connection(self.server, self.port)
        writer.write(f"NICK {self.nick}\r\nUSER {self.nick} 0 * :Adam Prism\r\n".encode())
        await writer.drain()
        for ch in self.channels_list:
            writer.write(f"JOIN {ch}\r\n".encode())
        await writer.drain()
        buffer = ""
        while self.running:
            try:
                data = await reader.read(4096)
                if not data:
                    break
                buffer += data.decode(errors="replace")
                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    if "PRIVMSG" in line and self.engine:
                        parts = line.split("!")
                        sender = parts[0].lstrip(":") if len(parts) > 1 else ""
                        text = line.split(":", 2)[-1] if "PRIVMSG" in line else ""
                        if text and sender != self.nick:
                            result = await self.engine.chat(text)
                            channel = line.split("PRIVMSG")[1].split(":")[0].strip() if "PRIVMSG" in line else self.channels_list[0]
                            for resp_line in result.get("response", "").split("\n"):
                                writer.write(f"PRIVMSG {channel} :{resp_line[:400]}\r\n".encode())
                            await writer.drain()
            except Exception as e:
                logger.error(f"IRC error: {e}")
            await asyncio.sleep(0.1)
        writer.close()

    async def send_message(self, target: str, text: str):
        logger.info(f"IRC message to {target}: {text[:30]}...")

    def stop(self):
        self.running = False


@_register
class XMPPChannel(BaseChannel):
    name = "xmpp"
    requires = ["jid", "password"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.jid = cfg.get("jid", "")
        self.password = cfg.get("password", "")

    async def start_polling(self):
        self.running = True
        logger.info(f"📡 XMPP channel for {self.jid} (requires slixmpp or aioxmpp)")

    async def send_message(self, target: str, text: str):
        logger.info(f"XMPP message to {target}: {text[:30]}...")


@_register
class TelegramWebhookChannel(BaseChannel):
    name = "telegram_webhook"
    requires = ["bot_token"]
    is_polling = False
    is_webhook = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.bot_token = cfg.get("bot_token", "")
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    async def start_polling(self):
        self.running = True
        logger.info("📡 Telegram webhook mode at /webhook/telegram")

    async def send_message(self, target: str, text: str):
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                for chunk in [text[i:i+4096] for i in range(0, len(text), 4096)]:
                    await client.post(f"{self.api_base}/sendMessage", json={"chat_id": int(target), "text": chunk})
            except Exception as e:
                logger.error(f"Telegram webhook send failed: {e}")

    def get_webhook_routes(self) -> list:
        return [{"path": "/webhook/telegram", "method": "POST", "handler": self._webhook_post}]

    async def _webhook_post(self, request) -> dict:
        data = await request.json()
        msg = data.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "")
        if chat_id and text and self.engine:
            result = await self.engine.chat(text)
            await self.send_message(str(chat_id), result.get("response", ""))
        return {"content": "OK", "status_code": 200}


@_register
class GenericWebhookChannel(BaseChannel):
    name = "webhook_generic"
    requires = []
    is_polling = False
    is_webhook = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.secret = cfg.get("secret", "")
        self.allowed_paths = cfg.get("allowed_paths", ["/webhook/generic"])

    async def start_polling(self):
        self.running = True
        logger.info("📡 Generic webhook at /webhook/generic")

    async def send_message(self, target: str, text: str):
        logger.info(f"Generic webhook send to {target}")

    def get_webhook_routes(self) -> list:
        return [{"path": "/webhook/generic", "method": "POST", "handler": self._webhook_post}]

    async def _webhook_post(self, request) -> dict:
        data = await request.json()
        msg = data.get("message", data.get("text", data.get("body", json.dumps(data))))
        if msg and self.engine:
            result = await self.engine.chat(str(msg))
            return {"content": json.dumps({"response": result.get("response", "")}, ensure_ascii=False), "status_code": 200}
        return {"content": "{}", "status_code": 200}


@_register
class RSSChannel(BaseChannel):
    name = "rss"
    requires = ["feeds"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.feeds = cfg.get("feeds", [])
        self._last_seen = {}

    async def start_polling(self):
        if not self.feeds:
            return
        self.running = True
        logger.info(f"📡 RSS polling {len(self.feeds)} feeds")
        import asyncio, httpx
        async with httpx.AsyncClient() as client:
            while self.running:
                for url in self.feeds:
                    try:
                        resp = await client.get(url, headers={"User-Agent": "adam-prism/1.0"})
                        text = resp.text
                        import hashlib
                        h = hashlib.md5(text.encode()).hexdigest()
                        if self._last_seen.get(url) != h:
                            self._last_seen[url] = h
                            logger.info(f"📰 RSS update from {url}")
                    except Exception as e:
                        logger.error(f"RSS error: {e}")
                await asyncio.sleep(300)

    async def send_message(self, target: str, text: str):
        pass


@_register
class NotionChannel(BaseChannel):
    name = "notion"
    requires = ["api_key"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.api_key = cfg.get("api_key", "")
        self.database_id = cfg.get("database_id", "")

    async def start_polling(self):
        if not self.api_key:
            return
        self.running = True
        logger.info("📡 Notion channel ready")

    async def send_message(self, target: str, text: str):
        if not self.api_key:
            return
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"https://api.notion.com/v1/pages",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
                             "Notion-Version": "2022-06-28"},
                    json={"parent": {"database_id": self.database_id or target},
                          "properties": {"title": {"title": [{"text": {"content": text[:100]}}]}}},
                )
            except Exception as e:
                logger.error(f"Notion send failed: {e}")


@_register
class GitHubChannel(BaseChannel):
    name = "github"
    requires = ["token"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.token = cfg.get("token", "")
        self.repos = cfg.get("repos", [])
        self._last_checked = {}

    async def start_polling(self):
        if not self.token or not self.repos:
            return
        self.running = True
        logger.info(f"📡 GitHub polling {len(self.repos)} repos")
        import asyncio, httpx
        async with httpx.AsyncClient() as client:
            while self.running:
                for repo in self.repos:
                    try:
                        resp = await client.get(
                            f"https://api.github.com/repos/{repo}/issues",
                            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github.v3+json"},
                            params={"state": "open", "sort": "updated", "per_page": 5},
                        )
                        issues = resp.json()
                        if isinstance(issues, list):
                            for issue in issues[:3]:
                                title = issue.get("title", "")
                                num = issue.get("number", 0)
                                logger.info(f"🐙 {repo}#{num}: {title}")
                    except Exception as e:
                        logger.error(f"GitHub poll error: {e}")
                await asyncio.sleep(300)

    async def send_message(self, target: str, text: str):
        if not self.token:
            return
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"https://api.github.com/repos/{target}/issues",
                    headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
                    json={"title": text[:256], "body": text},
                )
            except Exception as e:
                logger.error(f"GitHub issue creation failed: {e}")


@_register
class WeChatChannel(BaseChannel):
    name = "wechat"
    requires = ["corp_id", "corp_secret"]
    is_polling = True

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        cfg = config.get(self.name, config)
        self.corp_id = cfg.get("corp_id", "")
        self.corp_secret = cfg.get("corp_secret", "")
        self.agent_id = cfg.get("agent_id", "")

    async def start_polling(self):
        self.running = True
        logger.info("📡 WeChat Work channel ready")

    async def send_message(self, target: str, text: str):
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                token_resp = await client.get(
                    f"https://qyapi.weixin.qq.com/cgi-bin/gettoken",
                    params={"corpid": self.corp_id, "corpsecret": self.corp_secret},
                )
                token = token_resp.json().get("access_token", "")
                await client.post(
                    f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}",
                    json={"touser": target, "msgtype": "text", "agentid": self.agent_id, "text": {"content": text}},
                )
            except Exception as e:
                logger.error(f"WeChat send failed: {e}")
