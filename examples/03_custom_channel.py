#!/usr/bin/env python3
"""
Example 03: Custom Channel - إضافة قناة اتصال جديدة
====================================================
هذا المثال يوضح كيفية إضافة قناة مخصصة (مثل: Slack، Mattermost،
نظام تذاكر داخلي، إلخ) وربطها بـ Adam Prism.
"""

import asyncio
from typing import Any
from adam.channels.base import BaseChannel


class MyCustomChannel(BaseChannel):
    """مثال لقناة مخصصة - استبدل بالـ implementation الحقيقي"""
    
    name = "my-custom-channel"
    requires = ["api_token", "webhook_url"]  # إعدادات مطلوبة
    
    def __init__(self, config: dict, engine=None):
        super().__init__(config, engine)
        self.api_token = config.get("api_token", "")
        self.webhook_url = config.get("webhook_url", "")
        self.bot_user_id = config.get("bot_user_id", "")
    
    async def start_polling(self):
        """بدء الاستماع للرسائل الواردة"""
        print(f"🚀 بدء قناة {self.name}...")
        # هنا تضع الكود الحقيقي للـ polling أو webhook server
        # مثال:
        # async with aiohttp.ClientSession() as session:
        #     async with session.get(f"{self.webhook_url}/listen") as resp:
        #         async for msg in resp.content:
        #             await self._handle_incoming(msg)
        print(f"✅ قناة {self.name} تعمل وتستقبل الرسائل")
    
    async def send_message(self, chat_id: str, text: str, **kwargs) -> bool:
        """إرسال رسالة عبر القناة"""
        # هنا تضع كود الإرسال الحقيقي
        # مثال:
        # async with aiohttp.ClientSession() as session:
        #     await session.post(
        #         f"{self.webhook_url}/send",
        #         headers={"Authorization": f"Bearer {self.api_token}"},
        #         json={"channel": chat_id, "text": text}
        #     )
        print(f"📤 إرسال إلى {chat_id}: {text[:50]}...")
        return True
    
    async def _handle_incoming(self, raw_message: dict):
        """معالجة رسالة واردة وتحويلها للمحرك"""
        # استخراج البيانات
        user_id = raw_message.get("user", "")
        text = raw_message.get("text", "")
        channel_id = raw_message.get("channel", "")
        
        if not text or user_id == self.bot_user_id:
            return
        
        # استدعاء المحرك
        if self.engine:
            result = await self.engine.chat(text, context={"channel": self.name, "user_id": user_id})
            # إرسال الرد
            await self.send_message(channel_id, result["response"])


def register_channel():
    """تسجيل القناة في ChannelManager"""
    # في التطبيق الحقيقي، أضف إلى backend/adam/channels/bulk.py
    # أو استورد في manager.py
    
    # في bulk.py:
    # from .my_custom import MyCustomChannel
    # 
    # CHANNEL_REGISTRY["my-custom"] = MyCustomChannel
    
    print("📝 لتفعيل القناة:")
    print("   1. أضف الاستيراد في backend/adam/channels/bulk.py")
    print("   2. أضف إلى CHANNEL_REGISTRY")
    print("   3. أضف إعدادات في .env:")
    print("      MY_CUSTOM_API_TOKEN=xxx")
    print("      MY_CUSTOM_WEBHOOK_URL=xxx")
    print("   4. فعّلها في deploy/.env أو config")


async def main():
    print("🔧 Adam Prism - Custom Channel Example")
    print("=" * 50)
    register_channel()
    
    print()
    print("💡 الهيكل الأساسي:")
    print("   class MyCustomChannel(BaseChannel):")
    print("       name = 'my-custom-channel'")
    print("       requires = ['api_token', 'webhook_url']")
    print("       async def start_polling(self): ...")
    print("       async def send_message(self, chat_id, text): ...")


if __name__ == "__main__":
    asyncio.run(main())