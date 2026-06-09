# Channels — 25 قناة تواصل

## Overview

Three types of channels: Webhook, Polling, Hybrid.

| Type | Mechanism | Channels |
|------|-----------|----------|
| **Webhook** | يستقبل أحداث من service خارجي | WhatsApp, Facebook, Slack, LINE, Viber, Teams, Google Chat, Telegram Webhook, WebChat Widget, Generic Webhook |
| **Polling** | يسأل service كل X ثانية | Telegram, Twitter, Email, SMS, WebSocket, Matrix, Signal, IRC, XMPP, Instagram, WeChat, RSS, GitHub, Notion |
| **Hybrid** | Gateway + Webhook معاً | Discord |

## ChannelManager

`adam/channels/manager.py` — يدير كل القنوات:

```python
from adam.channels.manager import ChannelManager

manager = ChannelManager(config)
await manager.start_all()    # شغل كل القنوات
await manager.stop_all()     # أوقف الكل
```

كل channel عبارة عن class بيورث من `BaseChannel`:

```python
class BaseChannel:
    name: str
    channel_type: str  # "webhook" | "polling" | "hybrid"

    async def start(self): ...
    async def stop(self): ...
    async def send(self, message): ...
    async def receive(self): ...
```

## Webhook Channels

### WhatsApp (MCP-based)

- يستخدم MCP adapter للتواصل
- Webhook endpoint: `POST /webhook/whatsapp`
- Verification: signature-based

### Telegram Webhook

- Webhook endpoint: `POST /webhook/telegram`
- سهل الإعداد — ما يحتاجش polling

### Generic Webhook

- أي service يقدر يبعت webhook
- تنسيق JSON موحد

## Polling Channels

### Telegram (Polling)

- Long polling على Bot API
- بينفع لو الـ webhook مش متاح

### RSS

- يراقب RSS feeds
- configurable interval

### GitHub

- يراقب issues, PRs, notifications
- يستخدم GitHub API

### Email

- POP3/IMAP polling
- SMTP للإرسال

## Telegram Bot

Standalone microservice (`deploy/bot_entrypoint.py`):

```bash
python deploy/bot_entrypoint.py --token YOUR_BOT_TOKEN
```

أو كـ Docker container:

```yaml
services:
  telegram-bot:
    build:
      dockerfile: deploy/Dockerfile.api
    command: python deploy/bot_entrypoint.py
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
```

## WhatsApp Channel

MCP-based webhook adapter مع signature verification.

```python
from adam.channels.whatsapp import WhatsAppChannel

channel = WhatsAppChannel({
    "phone_number_id": "...",
    "access_token": "...",
    "verify_token": "...",
})
```

## WebChat Widget

Next.js component (in `web-ui/`) — يتصفح ويتكلم من المتصفح.

```tsx
import { AdamChat } from "@/components/adam-chat"

function Page() {
  return <AdamChat endpoint="http://localhost:8001" />
}
```

## Config Template

```json
{
  "channels": {
    "telegram": {
      "enabled": false,
      "bot_token": "",
      "mode": "webhook"
    },
    "whatsapp": {
      "enabled": false,
      "phone_number_id": "",
      "access_token": "",
      "verify_token": ""
    },
    "discord": {
      "enabled": false,
      "bot_token": ""
    },
    "webchat": {
      "enabled": true
    },
    "rss": {
      "enabled": false,
      "feeds": [],
      "interval": 300
    },
    "github": {
      "enabled": false,
      "token": "",
      "repos": []
    }
  }
}
```
