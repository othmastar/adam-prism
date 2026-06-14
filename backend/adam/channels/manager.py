"""
Adam Prism — Dynamic Channel Manager
=====================================
يكتشف القنوات المفعّلة في الكونفيج ويشغّلها أوتوماتيكيًا.
"""

import asyncio
import logging
from typing import Any

from .base import BaseChannel

logger = logging.getLogger("adam_prism.channels")

CHANNEL_REGISTRY: dict[str, type] = {}

def discover_channels():
    """يجيب كل الـ channels المسجلة"""
    global CHANNEL_REGISTRY
    if CHANNEL_REGISTRY:
        return CHANNEL_REGISTRY

    from . import telegram, whatsapp

    for mod in [telegram, whatsapp]:
        for attr in dir(mod):
            cls = getattr(mod, attr)
            if isinstance(cls, type) and issubclass(cls, BaseChannel) and cls is not BaseChannel:
                if cls.name:
                    CHANNEL_REGISTRY[cls.name] = cls

    from .bulk import BULK_CHANNELS

    for name, cls in BULK_CHANNELS.items():
        if name not in CHANNEL_REGISTRY:
            CHANNEL_REGISTRY[name] = cls

    return CHANNEL_REGISTRY

class ChannelManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.channels: dict[str, BaseChannel] = {}
        self._tasks = []
        self._webhook_routes = []

    async def start_all(self, engine=None):
        if not CHANNEL_REGISTRY:
            discover_channels()

        channels_cfg = self.config.get("channels", {})

        for name, cls in CHANNEL_REGISTRY.items():
            channel_cfg = channels_cfg.get(name, {})
            if not channel_cfg.get("enabled", False):
                continue
            if not cls.is_available({"channels": {name: channel_cfg}}):
                missing = cls.validate_config({"channels": {name: channel_cfg}})
                logger.warning(f"⚠️ {name}: missing {missing}, skipping")
                continue
            try:
                merged = {**self.config, name: channel_cfg}
                channel = cls(merged)
                if engine:
                    channel.attach_engine(engine)
                self.channels[name] = channel
                if channel.is_webhook:
                    self._webhook_routes.extend(channel.get_webhook_routes())
                logger.info(f"✅ {name} channel ready")
            except Exception:
                logger.exception("⚠️ {name} init failed:")

    async def start_polling_all(self):
        for name, channel in self.channels.items():
            if channel.is_polling and hasattr(channel, "start_polling"):
                task = asyncio.create_task(channel.start_polling(), name=f"ch-{name}")
                self._tasks.append(task)
                logger.info(f"📡 {name} polling started")

    async def stop_all(self):
        for _name, channel in self.channels.items():
            if hasattr(channel, "stop"):
                channel.stop()
        for task in self._tasks:
            task.cancel()
        logger.info("🛑 All channels stopped")

    def get_status(self) -> dict:
        return {name: ch.get_status() for name, ch in self.channels.items()}

    def get_webhook_routes(self) -> list:
        return self._webhook_routes
