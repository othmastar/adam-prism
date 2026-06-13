"""
Adam Prism — Multi-Channel Package (25+ channels)
==================================================
كل قنوات التواصل لآدم: Telegram, WhatsApp, Discord, Slack, Email, SMS,
WebSocket, WebChat, Twitter, Facebook, Matrix, Signal, Instagram, LINE,
Viber, Teams, Google Chat, IRC, XMPP, WeChat, Telegram Webhook, وغيرها.
"""

from .base import BaseChannel
from .bulk import BULK_CHANNELS
from .manager import CHANNEL_REGISTRY, ChannelManager, discover_channels
from .telegram import TelegramChannel
from .whatsapp import WhatsAppChannel

# Map channel names to their display class names for __getattr__
_CHANNEL_CLASS_NAMES = {
    "discord": "DiscordChannel",
    "slack": "SlackChannel",
    "email": "EmailChannel",
    "sms": "SMSChannel",
    "websocket": "WebSocketChannel",
    "webchat": "WebChatChannel",
    "twitter": "TwitterChannel",
    "facebook": "FacebookChannel",
    "matrix": "MatrixChannel",
    "signal": "SignalChannel",
    "instagram": "InstagramChannel",
    "line": "LINEChannel",
    "viber": "ViberChannel",
    "teams": "TeamsChannel",
    "googletalk": "GoogleChatChannel",
    "irc": "IRCChannel",
    "xmpp": "XMPPChannel",
    "telegram_webhook": "TelegramWebhookChannel",
    "wechat": "WeChatChannel",
    "webhook_generic": "GenericWebhookChannel",
    "rss": "RSSChannel",
    "notion": "NotionChannel",
    "github": "GitHubChannel",
}

def __getattr__(name):
    for ch_name, cls_name in _CHANNEL_CLASS_NAMES.items():
        if name == cls_name:
            cls = BULK_CHANNELS.get(ch_name)
            if cls:
                globals()[name] = cls
                return cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "BULK_CHANNELS",
    "CHANNEL_REGISTRY",
    "BaseChannel",
    "ChannelManager",
    "DiscordChannel",
    "EmailChannel",
    "FacebookChannel",
    "GenericWebhookChannel",
    "GitHubChannel",
    "GoogleChatChannel",
    "IRCChannel",
    "InstagramChannel",
    "LINEChannel",
    "MatrixChannel",
    "NotionChannel",
    "RSSChannel",
    "SMSChannel",
    "SignalChannel",
    "SlackChannel",
    "TeamsChannel",
    "TelegramChannel",
    "TelegramWebhookChannel",
    "TwitterChannel",
    "ViberChannel",
    "WeChatChannel",
    "WebChatChannel",
    "WebSocketChannel",
    "WhatsAppChannel",
    "XMPPChannel",
    "discover_channels",
]
