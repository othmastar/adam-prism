# Adam Prism - Examples

أمثلة عملية لاستخدام Adam Prism كـ framework.
كل مثال مستقل — شغّله بـ copy-paste.

## المتطلبات

```
pip install adam-prism
ollama pull adam-prism-v13:latest
docker run -p 6333:6333 qdrant/qdrant  # اختياري للـ RAG
```

## التشغيل

```
python 01_basic_chat.py
python 02_custom_provider.py
python 03_custom_channel.py
python 04_skill_creation.py
python 05_knowledge_rag.py
```

## القائمة

| # | الملف | الوصف |
|---|-------|-------|
| 01 | `01_basic_chat.py` | أبسط استخدام (مكتبة Python) |
| 02 | `02_custom_provider.py` | إضافة LLM provider مخصص |
| 03 | `03_custom_channel.py` | إضافة قناة اتصال جديدة |
| 04 | `04_skill_creation.py` | إنشاء Skills (ملفات Markdown) |
| 05 | `05_knowledge_rag.py` | RAG مع Qdrant (إضافة + بحث + محادثة) |
