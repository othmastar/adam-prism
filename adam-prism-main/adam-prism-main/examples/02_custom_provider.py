#!/usr/bin/env python3
"""
Example 02: Custom Provider - إضافة LLM provider مخصص
=======================================================
هذا المثال يوضح كيفية إضافة provider جديد (مثلاً: نموذج محلي مخصص،
أو API مختلف، أو proxy) واستخدامه مع Adam Prism.
"""

import asyncio
from typing import AsyncIterator
from adam.providers.base import BaseProvider
from adam import AdamPrismEngine


class MyCustomProvider(BaseProvider):
    """مثال لـ provider مخصص - يستبدل هذا بـ implementation حقيقي"""
    
    name = "my-custom-provider"
    model = "my-custom-model"
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("custom_api_key", "")
        self.base_url = config.get("custom_base_url", "http://localhost:8000")
    
    async def chat(self, messages: list[dict], **kwargs) -> dict:
        """تنفيذ محادثة غير متدفقة"""
        # هنا تضع استدعاء API الحقيقي
        # مثال باستخدام httpx:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(f"{self.base_url}/chat", json={"messages": messages})
        #     return response.json()
        
        # للاختبار: رد وهمي
        last_msg = messages[-1]["content"] if messages else ""
        return {
            "response": f"[Custom Provider] استلمت: {last_msg[:50]}...",
            "model": self.model,
        }
    
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        """توليد نص بسيط"""
        return f"[Custom Provider] Generated for: {prompt[:50]}..."
    
    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        """محادثة متدفقة (streaming)"""
        response = await self.chat(messages, **kwargs)
        # محاكاة streaming
        for chunk in response["response"].split(" "):
            yield chunk + " "
            await asyncio.sleep(0.05)


async def main():
    print("🔧 Adam Prism - Custom Provider Example")
    print("=" * 50)
    
    # تسجيل الـ provider المخصص
    # في التطبيق الحقيقي، أضفه إلى ProviderManager._create_provider()
    # أو استخدم config مخصص
    
    # إنشاء محرك مع إعدادات مخصصة
    config = {
        "inference_mode": "custom",
        "custom_provider_class": "examples.02_custom_provider.MyCustomProvider",
        "custom_api_key": "your-api-key-here",
        "custom_base_url": "http://localhost:8000",
        "qdrant_url": "http://localhost:6333",
    }
    
    # ملاحظة: لتشغيل هذا المثال فعلياً، تحتاج لتعديل ProviderManager
    # لإضافة الـ custom provider. هذا مثال توضيحي فقط.
    print("📝 هذا مثال توضيحي - لتفعيله:")
    print("   1. أضف provider إلى backend/adam/providers/manager.py")
    print("   2. أو مرر config مخصص مع provider class")
    print()
    print("💡 الهيكل الأساسي:")
    print(f"   class MyCustomProvider(BaseProvider):")
    print(f"       name = 'my-custom-provider'")
    print(f"       model = 'my-model'")
    print(f"       async def chat(self, messages, **kwargs): ...")
    print(f"       async def generate(self, prompt, system='', **kwargs): ...")
    print(f"       async def chat_stream(self, messages, **kwargs): ...")


if __name__ == "__main__":
    asyncio.run(main())