"""
Adam Prism — Base Channel Abstract Class
=========================================
توحيد واجهة كل القنوات: كل channel يورث من BaseChannel.
"""

from abc import ABC, abstractmethod
from typing import Any

class BaseChannel(ABC):
    name: str = ""
    requires: list[str] = []
    is_webhook: bool = False
    is_polling: bool = True

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.engine = None
        self.running = False

    def attach_engine(self, engine):
        self.engine = engine

    @abstractmethod
    async def start_polling(self):
        ...

    @abstractmethod
    async def send_message(self, target: str, text: str):
        ...

    def get_webhook_routes(self) -> list:
        return []

    def stop(self):
        self.running = False

    @classmethod
    def _channel_config(cls, config: dict[str, Any]) -> dict:
        cfg = config.get(cls.name, {})
        if not cfg:
            cfg = config.get("channels", {}).get(cls.name, {})
        if not cfg:
            cfg = config
        return cfg

    @classmethod
    def is_available(cls, config: dict[str, Any]) -> bool:
        cfg = cls._channel_config(config)
        return all(cfg.get(k) for k in cls.requires)

    @classmethod
    def validate_config(cls, config: dict[str, Any]) -> list[str]:
        cfg = cls._channel_config(config)
        missing = [f"{cls.name}.{k}" for k in cls.requires if not cfg.get(k)]
        return missing

    def get_status(self) -> dict:
        return {"name": self.name, "running": self.running, "webhook": self.is_webhook}
