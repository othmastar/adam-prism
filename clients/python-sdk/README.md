# Adam Prism Python SDK

**التوأم الرقمي الشخصي — Python Client**

A fully typed Python SDK (sync + async) for interacting with the Adam Prism API server.
عميل بايثون كامل الأنواع (متزامن + غير متزامن) للتفاعل مع خادم Adam Prism API.

---

## Installation / التنصيب

```bash
pip install adam-prism-client
```

Or from source / أو من المصدر:

```bash
git clone https://github.com/anomalyco/Adam_Prism_Complete_v2.git
cd Adam_Prism_Complete_v2/clients/python-sdk
pip install -e .
```

---

## Quick Start / بداية سريعة

### Sync / متزامن

```python
from adam_prism_client import AdamPrismClient

client = AdamPrismClient("http://localhost:8000")

# Chat — محادثة
result = client.chat("ما اسمك؟")
print(result["response"])

# System status — حالة النظام
status = client.get_status()
print(status)

# Search knowledge — بحث في المعرفة
results = client.search_knowledge("artificial intelligence")
for r in results.get("results", []):
    print(f"  [{r['id']}] {r['text'][:80]}")

# List sessions — قائمة الجلسات
sessions = client.list_sessions()

# Health check — فحص الصحة
health = client.get_system_health()
```

### Async / غير متزامن

```python
import asyncio
from adam_prism_client import AdamPrismClient

async def main():
    client = AdamPrismClient("http://localhost:8000")
    result = await client.chat_async("ما اسمك؟")
    print(result["response"])
    await client.close()

asyncio.run(main())
```

### Context Manager

```python
with AdamPrismClient("http://localhost:8000") as client:
    result = client.chat("السلام عليكم")
    print(result["response"])
```

---

## All Methods / كل الدوال

### Chat / المحادثة
| Method | Async | Description |
|--------|-------|-------------|
| `chat(message, context, voice)` | `chat_async()` | Send a message / إرسال رسالة |
| `chat_stream(message)` | `chat_stream_async()` | Streaming (SSE) / بث مباشر |

### Knowledge Base / قاعدة المعرفة
| Method | Async | Description |
|--------|-------|-------------|
| `search_knowledge(query, collection, top_k)` | ✓ | Search / بحث |
| `add_knowledge(text, collection)` | ✓ | Add text / إضافة نص |
| `upload_knowledge_file(filepath, collection)` | ✓ | Upload file (PDF/DOCX/TXT/MD) |
| `list_collections()` | ✓ | List Qdrant collections |

### Sessions / الجلسات
| Method | Async | Description |
|--------|-------|-------------|
| `list_sessions()` | ✓ | List all sessions |
| `create_session(title, first_message)` | ✓ | Create session |
| `get_session(session_id)` | ✓ | Get session with messages |
| `search_chat_history(query)` | ✓ | Search chat history |

### Skills / المهارات
| Method | Async | Description |
|--------|-------|-------------|
| `list_skills()` | ✓ | List available skills |
| `load_skill(path)` | ✓ | Load and run a skill |

### Plugins / الإضافات
| Method | Async | Description |
|--------|-------|-------------|
| `list_plugins()` | ✓ | List loaded plugins |
| `load_plugin(path)` | ✓ | Load plugin from path |

### Channels / القنوات
| Method | Async | Description |
|--------|-------|-------------|
| `list_channels()` | ✓ | List all channels |
| `get_channel(name)` | ✓ | Get channel status |
| `toggle_channel(name, enabled)` | ✓ | Toggle channel |

### System / النظام
| Method | Async | Description |
|--------|-------|-------------|
| `get_status()` | ✓ | Engine status |
| `get_system_health()` | ✓ | Health check |
| `get_metrics()` | ✓ | Performance metrics |
| `get_diagnostics()` | ✓ | Self-diagnostics |
| `get_memory_stats()` | ✓ | Memory statistics |
| `get_notebook_stats()` | ✓ | Notebook statistics |
| `get_security_stats()` | ✓ | Security statistics |
| `list_scheduled_jobs()` | ✓ | Scheduled jobs |

### Ollama
| Method | Async | Description |
|--------|-------|-------------|
| `list_ollama_models()` | ✓ | List Ollama models |
| `select_ollama_model(model)` | ✓ | Switch active model |

### Voice / الصوت
| Method | Async | Description |
|--------|-------|-------------|
| `transcribe_audio(filepath)` | ✓ | Speech-to-text |

---

## Error Handling / معالجة الأخطاء

```python
from adam_prism_client import (
    AdamPrismClient,
    NotFoundError,
    ServiceUnavailableError,
    APIError,
)

client = AdamPrismClient("http://localhost:8000")

try:
    session = client.get_session("nonexistent-id")
except NotFoundError as e:
    print(f"Not found: {e}")
except ServiceUnavailableError as e:
    print(f"Service down: {e}")
except APIError as e:
    print(f"API error {e.status_code}: {e.detail}")
```

---

## Typed Models / النماذج

```python
from adam_prism_client import ChatResponse, SkillsResponse

# Parse raw response into typed dataclass
data = client.chat("hello")
chat = ChatResponse.from_dict(data)
print(chat.response)
print(f"Mode: {chat.mode}, Tools: {chat.tools_used}")

skills_data = client.list_skills()
skills = SkillsResponse.from_dict(skills_data)
for skill in skills.skills:
    print(f"{skill.name}: {skill.description}")
```

---

## Requirements / المتطلبات
- Python ≥ 3.10
- httpx ≥ 0.27

---

## License / الترخيص
Apache 2.0
