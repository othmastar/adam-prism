#!/usr/bin/env python3
"""
Example 05: Knowledge RAG - البحث في قاعدة المعرفة مع Qdrant
=============================================================
هذا المثال يوضح كيفية استخدام RAG (Retrieval-Augmented Generation)
مع Adam Prism لإضافة معرفة جديدة والبحث فيها.
"""

import asyncio
from adam import AdamPrismEngine


async def add_knowledge_example():
    """إضافة معرفة جديدة إلى Qdrant"""
    engine = AdamPrismEngine(config={
        "inference_mode": "ollama",
        "ollama_base": "http://localhost:11434",
        "qdrant_url": "http://localhost:6333",
    })

    # التأكد من تشغيل Qdrant
    print("📚 إضافة معرفة جديدة...")

    # إضافة نصوص متعددة
    texts_to_add = [
        "آدم بريزم يدعم 4 أوضاع معرفية: محلل استراتيجي، باحث تقني، مطور برمجيات، معلم.",
        "نظام الأمان 3 طبقات: InputGuard يفحص المدخلات، OutputGuard يفحص المخرجات، ToolPermissionValidator يفحص الأدوات.",
        "بوابة الأخلاق تعتمد على 4 قوانين: العدالة 40%، نشر العلم 30%، البقاء 20%، الإبداع 10%.",
        "Adam Prism يدعم 23 قناة اتصال: Telegram، WhatsApp، Discord، Slack، Teams، Signal، Matrix، وغيرها.",
        "البوابة الأخلاقية تعتمد على 4 قوانين مرجحة: العدالة 40%، نشر العلم 30%، البقاء والحماية 20%، الإبداع 10%.",
    ]

    if engine.knowledge:
        for text in texts_to_add:
            ok = await engine.knowledge.store(
                collection="adam_knowledge",
                text=text,
                metadata={"source": "examples", "language": "ar"}
            )
            print(f"   {'✅' if ok else '❌'} {text[:60]}...")

    print()


async def search_knowledge_example():
    """البحث في قاعدة المعرفة"""
    engine = AdamPrismEngine(config={
        "inference_mode": "ollama",
        "ollama_base": "http://localhost:11434",
        "qdrant_url": "http://localhost:6333",
    })

    queries = [
        "ما هي طبقات الأمان في آدم؟",
        "How many channels does Adam Prism support?",
        "Explain the ethics gate weights",
        "ما هي طرق توسيع آدم بريزم؟",
    ]

    print("🔍 البحث في قاعدة المعرفة...")
    print("=" * 50)

    for query in queries:
        print(f"\n❓ السؤال: {query}")

        if engine.knowledge:
            results = await engine.knowledge.search(
                query=query,
                collection="adam_knowledge",
                top_k=3,
                score_threshold=0.0
            )

            if results:
                for i, result in enumerate(results, 1):
                    score = result.get("score", 0)
                    text = result.get("text", "")[:100]
                    print(f"   {i}. [score={score:.2f}] {text}...")
            else:
                print("   لا توجد نتائج")
        else:
            print("   ⚠️ Knowledge system غير متاح - تأكد من تشغيل Qdrant")


async def rag_chat_example():
    """محادثة مدعومة بـ RAG"""
    engine = AdamPrismEngine(config={
        "inference_mode": "ollama",
        "ollama_base": "http://localhost:11434",
        "qdrant_url": "http://localhost:6333",
    })

    print("\n💬 محادثة مدعومة بـ RAG:")
    print("=" * 50)

    message = "اشرح لي نظام الأمان في آدم بريزم"
    print(f"👤: {message}")

    # المحرك يستخدم knowledge.search تلقائياً قبل التوليد
    result = await engine.chat(message)

    print(f"🤖: {result['response']}")
    print(f"📊 المعرفة المستخدمة: {result.get('knowledge_used', 0)}")


async def main():
    print("🧠 Adam Prism - Knowledge RAG Example")
    print("=" * 50)
    print("تأكد من تشغيل Qdrant: docker run -p 6333:6333 qdrant/qdrant")
    print()

    # 1. إضافة معرفة
    await add_knowledge_example()

    # 2. البحث
    await search_knowledge_example()

    # 3. محادثة مع RAG
    await rag_chat_example()

    # 4. عبر REST API
    print("\n🌐 عبر REST API:")
    print("   # إضافة معرفة:")
    print('   curl -X POST http://localhost:8001/api/knowledge/add \\')
    print('     -H "Authorization: Bearer YOUR_API_KEY" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"texts": ["نص 1", "نص 2"], "collection": "knowledge"}\'')
    print()
    print("   # البحث:")
    print('   curl -X POST http://localhost:8001/api/knowledge/search \\')
    print('     -H "Authorization: Bearer YOUR_API_KEY" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "سؤالك", "collection": "knowledge", "top_k": 3}\'')


if __name__ == "__main__":
    asyncio.run(main())