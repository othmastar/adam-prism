#!/usr/bin/env python3
"""
Example 01: Basic Chat - أبسط استخدام لـ Adam Prism
=====================================================
هذا المثال يوضح كيفية استخدام Adam Prism Engine مباشرة
كـ Python library لإجراء محادثة بسيطة.
"""

import asyncio
from adam import AdamPrismEngine


async def main():
    # تهيئة المحرك مع إعدادات افتراضية (Ollama محلياً)
    engine = AdamPrismEngine(config={
        "inference_mode": "ollama",
        "model_name": "adam-prism-v13:latest",
        "ollama_base": "http://localhost:11434",
        "qdrant_url": "http://localhost:6333",
    })

    print("🤖 Adam Prism - Basic Chat Example")
    print("=" * 50)
    print("تأكد من تشغيل Ollama ووجود النموذج: ollama pull adam-prism-v13:latest")
    print("أو غير inference_mode إلى 'openai' مع API key")
    print()

    # محادثة بسيطة
    message = "مرحباً آدم، من أنت وماذا تقدر تعمل؟"
    print(f"👤 المستخدم: {message}")

    result = await engine.chat(message)

    print(f"🤖 آدم: {result['response']}")
    print()
    print(f"📊 تفاصيل:")
    print(f"   - الوضع: {result['mode']}")
    print(f"   - النية: {result['intent']}")
    print(f"   - المعرفة المستخدمة: {result['knowledge_used']}")
    print(f"   - الأدوات المستدعاة: {result['tool_calls_made']}")
    print(f"   - مدة المعالجة: {result.get('duration_ms', 'N/A')}ms")


if __name__ == "__main__":
    asyncio.run(main())