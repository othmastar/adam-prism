"""Tests for adam/channels/ package (25+ channels)"""

import pytest
from adam.channels.base import BaseChannel
from adam.channels.telegram import TelegramChannel
from adam.channels.whatsapp import WhatsAppChannel
from adam.channels.manager import ChannelManager, discover_channels

class TestBaseChannel:
    def test_abstract_cant_instantiate(self):
        with pytest.raises(TypeError):
            BaseChannel({})

    def test_concrete_works(self):
        ch = TelegramChannel({"telegram": {"bot_token": "x"}})
        assert ch.name == "telegram"
        assert ch.running is False

    def test_attach_engine(self):
        ch = TelegramChannel({"telegram": {"bot_token": "x"}})
        ch.attach_engine("fake")
        assert ch.engine == "fake"

    def test_stop(self):
        ch = TelegramChannel({"telegram": {"bot_token": "x"}})
        ch.running = True
        ch.stop()
        assert ch.running is False

    def test_is_available(self):
        assert TelegramChannel.is_available({"channels": {"telegram": {"bot_token": "x"}}}) is True
        assert TelegramChannel.is_available({"channels": {"telegram": {}}}) is False

    def test_validate_config(self):
        missing = TelegramChannel.validate_config({"channels": {"telegram": {}}})
        assert "telegram.bot_token" in missing

    def test_get_status(self):
        ch = TelegramChannel({"telegram": {"bot_token": "x"}})
        s = ch.get_status()
        assert s["name"] == "telegram"
        assert s["running"] is False

class TestTelegramChannel:
    def test_init_no_token(self):
        ch = TelegramChannel({"telegram": {"bot_token": ""}})
        assert ch.bot_token == ""

    def test_init_fallback_config(self):
        ch = TelegramChannel({"telegram_bot_token": "123:abc"})
        assert ch.bot_token == "123:abc"

class TestWhatsAppChannel:
    def test_init(self):
        ch = WhatsAppChannel({"whatsapp": {}})
        assert ch.running is False

    def test_verify_webhook_success(self):
        ch = WhatsAppChannel({"whatsapp": {"webhook_verify_token": "tok"}})
        assert ch.verify_webhook("subscribe", "tok", "ch") == "ch"

    def test_verify_webhook_failure(self):
        ch = WhatsAppChannel({"whatsapp": {"webhook_verify_token": "tok"}})
        assert ch.verify_webhook("subscribe", "wrong", "ch") is None

    def test_verify_signature_no_secret(self):
        ch = WhatsAppChannel({"whatsapp": {}})
        assert ch.verify_signature(b"hello", "sig") is False

    def test_verify_signature_valid(self):
        ch = WhatsAppChannel({"whatsapp": {"app_secret": "secret"}})
        import hmac
        import hashlib
        body = b'{"test": true}'
        expected = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
        assert ch.verify_signature(body, f"sha256={expected}") is True

    def test_verify_signature_invalid(self):
        ch = WhatsAppChannel({"whatsapp": {"app_secret": "secret"}})
        assert ch.verify_signature(b"body", "sha256:wrong") is False

    def test_webhook_routes(self):
        ch = WhatsAppChannel({"whatsapp": {}})
        routes = ch.get_webhook_routes()
        assert len(routes) == 2
        assert routes[0]["path"] == "/webhook/whatsapp"

class TestDiscovery:
    def test_discover_returns_telegram_whatsapp(self):
        registry = discover_channels()
        assert "telegram" in registry
        assert "whatsapp" in registry

    def test_discover_includes_bulk(self):
        registry = discover_channels()
        assert "discord" in registry
        assert "slack" in registry
        assert "email" in registry
        assert "sms" in registry
        assert "websocket" in registry
        assert "webchat" in registry
        assert "twitter" in registry
        assert "facebook" in registry
        assert "matrix" in registry
        assert "signal" in registry

    def test_bulk_light_adapters(self):
        light = ["instagram", "line", "viber", "teams", "googletalk", "irc", "xmpp", "telegram_webhook", "wechat"]
        registry = discover_channels()
        for name in light:
            assert name in registry, f"{name} missing from registry"

    def test_total_channels(self):
        registry = discover_channels()
        assert len(registry) >= 21, f"Got {len(registry)}, expected >= 21"

class TestChannelManager:
    def test_init(self):
        mgr = ChannelManager({})
        assert mgr.channels == {}

    def test_start_all_empty_config(self):
        mgr = ChannelManager({"channels": {}})

        async def run():
            await mgr.start_all()
            assert mgr.channels == {}

        import asyncio
        asyncio.run(run())

    def test_start_all_enabled(self):
        mgr = ChannelManager({
            "channels": {
                "telegram": {"enabled": True, "bot_token": "x"},
                "whatsapp": {"enabled": True, "phone_number_id": "123", "access_token": "abc"},
            }
        })

        async def run():
            await mgr.start_all()
            assert "telegram" in mgr.channels
            assert "whatsapp" in mgr.channels

        import asyncio
        asyncio.run(run())

    def test_start_skip_missing_config(self):
        mgr = ChannelManager({
            "channels": {
                "telegram": {"enabled": True},
            }
        })

        async def run():
            await mgr.start_all()
            assert "telegram" not in mgr.channels

        import asyncio
        asyncio.run(run())

    def test_stop_all(self):
        mgr = ChannelManager({
            "channels": {"telegram": {"enabled": True, "bot_token": "x"}}
        })

        async def run():
            await mgr.start_all()
            await mgr.stop_all()
            assert not mgr.channels["telegram"].running

        import asyncio
        asyncio.run(run())

    def test_get_status(self):
        mgr = ChannelManager({
            "channels": {"telegram": {"enabled": True, "bot_token": "x"}}
        })

        async def run():
            await mgr.start_all()
            status = mgr.get_status()
            assert "telegram" in status

        import asyncio
        asyncio.run(run())

    def test_webhook_routes_collected(self):
        mgr = ChannelManager({
            "channels": {
                "whatsapp": {"enabled": True, "phone_number_id": "123", "access_token": "abc"},
            }
        })

        async def run():
            await mgr.start_all()
            routes = mgr.get_webhook_routes()
            assert len(routes) >= 2

        import asyncio
        asyncio.run(run())

class TestNewChannels:
    @pytest.mark.parametrize("name,cls", [
        ("discord", "DiscordChannel"),
        ("slack", "SlackChannel"),
        ("email", "EmailChannel"),
        ("sms", "SMSChannel"),
        ("websocket", "WebSocketChannel"),
        ("webchat", "WebChatChannel"),
        ("twitter", "TwitterChannel"),
        ("facebook", "FacebookChannel"),
        ("matrix", "MatrixChannel"),
        ("signal", "SignalChannel"),
        ("instagram", "InstagramChannel"),
        ("line", "LINEChannel"),
        ("viber", "ViberChannel"),
        ("teams", "TeamsChannel"),
        ("googletalk", "GoogleChatChannel"),
        ("irc", "IRCChannel"),
        ("xmpp", "XMPPChannel"),
        ("telegram_webhook", "TelegramWebhookChannel"),
        ("wechat", "WeChatChannel"),
        ("webhook_generic", "GenericWebhookChannel"),
        ("rss", "RSSChannel"),
        ("notion", "NotionChannel"),
        ("github", "GitHubChannel"),
    ])
    def test_channel_basic_interface(self, name, cls):
        registry = discover_channels()
        ch_class = registry.get(name)
        assert ch_class is not None, f"{name} not in registry"
        assert ch_class.name == name

        ch = ch_class({"channels": {name: {}}})
        assert hasattr(ch, "start_polling")
        assert hasattr(ch, "send_message")
        assert hasattr(ch, "stop")
        assert hasattr(ch, "attach_engine")
        assert hasattr(ch, "get_status")
        assert hasattr(ch, "get_webhook_routes")
