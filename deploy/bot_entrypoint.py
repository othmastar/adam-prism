"""
Adam Prism — Bot Entrypoint (Telegram / WhatsApp)
==================================================
بيستخدم لبدء bot مستقل متصل بالمحرك.
للـ Docker: BOT_MODE=telegram or BOT_MODE=whatsapp
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("adam_prism.bot")

BOT_MODE = os.environ.get("BOT_MODE", "telegram")


async def main():
    # Load config
    config_path = Path(__file__).parent.parent / "config" / "default.json"
    config = {}
    if config_path.exists():
        import json
        with open(config_path) as f:
            config = json.load(f)

    # Environment overrides
    env_map = {
        "OLLAMA_BASE": "ollama_base",
        "QDRANT_URL": "qdrant_url",
        "TELEGRAM_BOT_TOKEN": "telegram_bot_token",
        "TELEGRAM_ENABLED": "telegram_enabled",
        "WHATSAPP_PHONE_NUMBER_ID": "whatsapp_phone_number_id",
        "WHATSAPP_ACCESS_TOKEN": "whatsapp_access_token",
        "WHATSAPP_WEBHOOK_VERIFY_TOKEN": "whatsapp_webhook_verify_token",
        "WHATSAPP_APP_SECRET": "whatsapp_app_secret",
        "AUTHORIZED_CHAT_IDS": "authorized_chat_ids",
    }
    for env_key, config_key in env_map.items():
        if env_key in os.environ:
            val = os.environ[env_key]
            if config_key == "telegram_enabled":
                config[config_key] = val.lower() in ("true", "1", "yes")
            elif config_key == "authorized_chat_ids":
                config[config_key] = json.loads(val) if val.startswith("[") else []
            else:
                config[config_key] = val

    # Initialize engine
    from core.engine import AdamPrismEngine
    engine = AdamPrismEngine(config)

    if BOT_MODE == "telegram":
        await _start_telegram(config, engine)
    elif BOT_MODE == "whatsapp":
        await _start_whatsapp(config, engine)
    else:
        logger.error(f"Unknown BOT_MODE: {BOT_MODE}")
        sys.exit(1)


async def _start_telegram(config: dict, engine):
    from adam.channels.telegram import TelegramChannel
    channel = TelegramChannel(config)
    channel.attach_engine(engine)
    await channel.start_polling()


async def _start_whatsapp(config: dict, engine):
    from adam.channels.whatsapp import WhatsAppChannel
    channel = WhatsAppChannel(config)
    channel.attach_engine(engine)
    await channel.start_polling()
    # WhatsApp يعتمد على webhooks — يفضل استخدام API
    logger.info("WhatsApp webhook mode — start API server to receive messages")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"Bot failed: {e}")
        sys.exit(1)
