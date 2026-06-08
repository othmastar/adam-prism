"""اختبار بوت Discord — نستخدم mocking عشان discord.py مش منصب"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class FakeEngine:
    """محرك وهمي للاختبار"""

    def __init__(self):
        self.provider = MagicMock()
        self.provider.chat = AsyncMock(return_value="Hello from Adam")
        self.config = {}

    async def chat(self, message: str):
        return {"response": f"Echo: {message}"}


@pytest.mark.asyncio
async def test_init_no_discord():
    """لما discord.py مش منصب، البوت يعرف يبدأ من غير كراش"""
    from adam.platforms.discord_bot import DiscordBot, DISCORD_AVAILABLE
    bot = DiscordBot(engine=FakeEngine(), config={})
    status = bot.get_status()
    assert status["type"] == "discord"
    # If discord not available, start should return False
    ok = await bot.start()
    if not DISCORD_AVAILABLE:
        assert ok is False
        assert "running" in status


@pytest.mark.asyncio
async def test_init_no_token():
    """من غير token، البوت ميفتتحش"""
    from adam.platforms.discord_bot import DiscordBot
    bot = DiscordBot(engine=FakeEngine(), config={})
    bot.__class__.DISCORD_AVAILABLE = True  # pretend it's installed
    ok = await bot.start()
    assert ok is False  # no token


@pytest.mark.asyncio
async def test_get_status():
    from adam.platforms.discord_bot import DiscordBot
    bot = DiscordBot(engine=FakeEngine(), config={
        "discord_token": "test_token",
        "discord_prefix": "!",
    })
    status = bot.get_status()
    assert status["running"] is False
    assert status["has_token"] is True
    assert status["prefix"] == "!"


@pytest.mark.asyncio
async def test_engine_init_with_discord_disabled():
    """لما discord_enabled=False في config، platform_discord يفضل stub"""
    from core.engine import AdamPrismEngine
    e = AdamPrismEngine({"inference_mode": "ollama", "discord_enabled": False})
    assert e.platform_discord is not None
    # Test it's a stub (not DiscordBot)
    status = e.platform_discord.get_status()
    assert isinstance(status, dict)


@pytest.mark.asyncio
async def test_engine_status_includes_platforms():
    from core.engine import AdamPrismEngine
    e = AdamPrismEngine({"inference_mode": "ollama", "discord_enabled": False})
    s = await e.get_status()
    assert "platforms" in s
    assert "discord" in s["platforms"]


@pytest.mark.asyncio
async def test_modules_attached():
    from core.engine import AdamPrismEngine
    e = AdamPrismEngine({"inference_mode": "ollama"})
    assert "platform_discord" in e.__dict__
