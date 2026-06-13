"""
Adam Prism — Discord Bot
=========================
يربط آدم بـ Discord: أوامر نصية، محادثة لكل server/channel، صلاحيات.
مش شرط يكون discord.py منصب — بيشتغل بـ try/except.
"""

import logging
from typing import Any

logger = logging.getLogger("adam_prism.platforms.discord")

try:
    import discord
    from discord.ext import commands as discord_commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    logger.info("discord.py مش منصب — Discord bot مش هينفع يشتغل")
    # Mock classes for type hints
    class discord:  # noqa: N801 — mock mimicking library name
        class Intents:
            def default(self): return None
        class Message: pass
    class discord_commands:  # noqa: N801 — mock mimicking library name
        class Bot: pass


class DiscordBot:
    """بوت Discord لآدم — محادثة في كل سيرفر"""

    def __init__(self, engine, config: dict[str, Any] | None = None):
        self.engine = engine
        self.config = config or {}
        self.token = self.config.get("discord_token", "")
        self.prefix = self.config.get("discord_prefix", "!")
        self.allowed_channels = self.config.get("discord_allowed_channels", [])
        self.allowed_roles = self.config.get("discord_allowed_roles", [])
        self.bot = None
        self._running = False
        self._task = None

    async def start(self):
        """تشغيل البوت"""
        if not DISCORD_AVAILABLE:
            logger.warning("⚠️ discord.py مش منصب — البوت مش هيفتتح")
            return False
        if not self.token:
            logger.warning("⚠️ Discord token مش موجود في config")
            return False
        if self._running:
            return True

        try:
            intents = discord.Intents.default()
            intents.message_content = True
            self.bot = discord_commands.Bot(command_prefix=self.prefix, intents=intents)

            @self.bot.event
            async def on_ready():
                logger.info(f"✅ Discord bot logged in as {self.bot.user}")

            @self.bot.event
            async def on_message(message):
                if message.author == self.bot.user:
                    return
                await self._handle_message(message)

            self._task = self.bot.start(self.token)
            # This won't block — discord.py handles its own loop
            # But we need to start it in background
            self._running = True
            logger.info("✅ Discord bot started")
            return True
        except Exception:
            logger.exception("⚠️ Discord bot start failed:")
            return False

    async def stop(self):
        """إيقاف البوت"""
        if self.bot and self._running:
            try:
                await self.bot.close()
            except Exception:
                logger.exception("⚠️ Discord bot close error:")
        self._running = False
        logger.info("Discord bot stopped")

    async def _handle_message(self, message):
        """معالجة رسالة Discord — استدعاء engine.chat()"""
        if not self.engine:
            return

        # فحص القنوات المسموحة
        if self.allowed_channels and message.channel.id not in self.allowed_channels:
            return

        # فحص الرتب المسموحة (اختياري)
        if self.allowed_roles and isinstance(message.author, discord.Member):
            user_roles = [r.id for r in message.author.roles]
            if not any(rid in user_roles for rid in self.allowed_roles):
                return

        user_msg = message.content
        if user_msg.startswith(self.prefix):
            user_msg = user_msg[len(self.prefix):].strip()

        if not user_msg:
            return

        try:
            async with message.channel.typing():
                result = await self.engine.chat(user_msg)
                response = result.get("response", "...")
                # Discord max 2000 chars per message
                if len(response) > 1900:
                    response = response[:1900] + "\n\n... [تم تقصير الرد]"
                await message.channel.send(response)
        except Exception as e:
            logger.exception("⚠️ Discord message handling error:")
            await message.channel.send(f"⚠️ خطأ: {e}")

    def get_status(self) -> dict[str, Any]:
        return {
            "type": "discord",
            "running": self._running,
            "discord_available": DISCORD_AVAILABLE,
            "has_token": bool(self.token),
            "prefix": self.prefix,
            "allowed_channels": len(self.allowed_channels),
            "allowed_roles": len(self.allowed_roles),
        }
