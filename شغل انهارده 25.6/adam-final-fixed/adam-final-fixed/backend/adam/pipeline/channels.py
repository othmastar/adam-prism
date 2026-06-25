"""
Adam Prism - نظام القناة (Tailscale + Telegram)
================================================
التواصل مع آدم من أي جهاز عبر:
- Tailscale VPN (واجهة ويب خاصة)
- Telegram Bot (رسائل فورية)
"""

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger("adam_prism.pipeline.channels")

class TelegramChannel:
    """
    قناة Telegram Bot.

    كيف يعمل:
    1. تنشئ Bot عبر @BotFather → تحصل على token
    2. آدم يستمع للرسائل الواردة
    3. كل رسالة تُعالج عبر المحرك الرئيسي
    4. الرد يُرسل عبر Telegram

    المميزات:
    - يعمل من التليفون مباشرة
    - إشعارات فورية
    - يدعم ملفات وصور وصوت
    - يعمل كقناة احتياطية لو Tailscale ما اشتغل
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.bot_token = config.get("telegram_bot_token", "")
        self.authorized_chat_ids = config.get("authorized_chat_ids", [])
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"
        self.engine = None  # سيتم ربطه
        self.running = False
        self.last_update_id = 0

        # معالجات الرسائل
        self.message_handlers = {
            "text": [],
            "document": [],
            "photo": [],
            "voice": []
        }

    def attach_engine(self, engine):
        """ربط المحرك الرئيسي"""
        self.engine = engine

    async def start_polling(self):
        """بدء الاستماع للرسائل (long polling)"""
        if not self.bot_token:
            logger.warning("لا يوجد Telegram Bot Token. قم بتعيينه في الإعدادات.")
            return

        self.running = True
        logger.info("بدء الاستماع على Telegram...")

        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            while self.running:
                try:
                    response = await client.get(
                        f"{self.api_base}/getUpdates",
                        params={
                            "offset": self.last_update_id + 1,
                            "timeout": 30
                        }
                    )

                    updates = response.json().get("result", [])

                    for update in updates:
                        self.last_update_id = update.get("update_id", 0)
                        await self._process_update(update)

                except Exception:
                    logger.exception("خطأ في polling:")
                    import asyncio
                    await asyncio.sleep(5)

    async def _process_update(self, update: dict):
        """معالجة رسالة واردة"""
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")

        # فحص المصادقة
        if self.authorized_chat_ids and chat_id not in self.authorized_chat_ids:
            await self.send_message(chat_id, "⛔ غير مصرح بالوصول.")
            return

        # معالجة حسب النوع
        if "text" in message:
            await self._handle_text(chat_id, message["text"])
        elif "document" in message:
            await self._handle_document(chat_id, message["document"])
        elif "voice" in message:
            await self._handle_voice(chat_id, message["voice"])

    async def _handle_text(self, chat_id: int, text: str):
        """معالجة رسالة نصية"""
        if self.engine:
            result = await self.engine.chat(text)
            await self.send_message(chat_id, result.get("response", ""))
        else:
            await self.send_message(chat_id, "المحرك غير متصل.")

    async def _handle_document(self, chat_id: int, document: dict):
        """معالجة ملف مرسل"""
        file_id = document.get("file_id")
        file_name = document.get("file_name", "unknown")

        # تحميل الملف
        import httpx
        async with httpx.AsyncClient(timeout=120.0) as client:
            file_info = await client.get(f"{self.api_base}/getFile?file_id={file_id}")
            file_path = file_info.json().get("result", {}).get("file_path", "")

            if file_path:
                download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                response = await client.get(download_url)

                save_path = f"./received_files/{file_name}"
                import os
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                with open(save_path, "wb") as f:
                    f.write(response.content)

                await self.send_message(chat_id, f"تم استلام الملف: {file_name}")

    async def _handle_voice(self, chat_id: int, voice: dict):
        """معالجة رسالة صوتية"""
        await self.send_message(chat_id, "🔊 الرسائل الصوتية ستكون متاحة قريباً.")

    async def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown"):
        """إرسال رسالة عبر Telegram"""
        if not self.bot_token:
            return

        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # تقسيم الرسائل الطويلة
                max_length = 4096
                chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]

                for chunk in chunks:
                    await client.post(
                        f"{self.api_base}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": chunk,
                            "parse_mode": parse_mode
                        }
                    )
            except Exception:
                logger.exception("تعذر إرسال رسالة Telegram:")

    def stop(self):
        """إيقاف الاستماع"""
        self.running = False

class TailscaleConfig:
    """
    إعدادات Tailscale VPN.

    Tailscale يتيح:
    - شبكة خاصة بين كل أجهزتك
- IP ثابت لكل جهاز
    - وصول من أي مكان في العالم
    - تشفير WireGuard تلقائي

    بعد التثبيت:
    - من التليفون: http://100.x.x.x:3000
    - من iPad: http://100.x.x.x:3000
    - من PC: http://100.x.x.x:3000
    """

    @staticmethod
    def get_setup_instructions() -> str:
        """تعليمات إعداد Tailscale"""
        return """
# إعداد Tailscale VPN

## 1. التثبيت
```bash
# على Linux (سيرفر آدم)
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# على Windows
# حمّل من: https://tailscale.com/download/windows

# على Mac
# حمّل من: https://tailscale.com/download/mac

# على iOS (تليفون/iPad)
# من App Store: ابحث عن Tailscale
```

## 2. الحصول على IP
```bash
# على السيرفر
tailscale ip -4
# مثال: 100.64.0.1
```

## 3. الوصول
- من أي جهاز: http://100.64.0.1:3000 (الواجهة)
- API: http://100.64.0.1:8000 (API)

## 4. الأمان
- فعّل MagicDNS للوصول بالاسم بدل IP
- استخدم Tailscale ACLs لتقييد الوصول
- فعّل exit node لو حابب تمر كل الترافيك
"""

    @staticmethod
    async def get_status() -> dict:
        """حالة Tailscale"""
        # [PHASE2] async subprocess instead of blocking subprocess.run
        try:
            proc = await asyncio.create_subprocess_exec(
                "tailscale", "status", "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            except TimeoutError:
                proc.kill()
                await proc.wait()
                return {"status": "timeout"}
            if proc.returncode == 0:
                return json.loads(stdout.decode("utf-8", errors="replace"))
        except FileNotFoundError:
            return {"status": "not_installed"}
        except Exception as e:
            logger.debug("tailscale status check failed: %s", e)

        return {"status": "not_installed_or_not_running"}
