"""
Adam Prism — Final Test Suite
==============================
يختبر كل الإصلاحات في بيئة افتراضية مع mock Ollama.

الاختبارات:
1. engine.py - pipeline + fallback chain + stats
2. server_minimal.py - endpoints + engine_ready + heal
3. file upload - مع session_id
4. STT/TTS endpoints
5. memory system (LTM)
6. tools execution
7. session management
"""

import asyncio
import json
import os
import sys
import subprocess
import time
from pathlib import Path

# إعدادات
os.environ["ADAM_OLLAMA_URL"] = "http://localhost:11434"
os.environ["ADAM_OLLAMA_MODEL"] = "qwen2.5:0.5b"  # الموديل الأساسي
os.environ["ADAM_OLLAMA_FALLBACK_MODEL"] = "qwen2.5:0.5b"
os.environ["ADAM_AUXILIARY_MODEL"] = "qwen2.5:0.5b"
os.environ["ADAM_SESSION_DB"] = "/tmp/adam_test_final_sessions.db"
os.environ["ADAM_MEMORY_DB"] = "/tmp/adam_test_final_memory.db"
os.environ["ADAM_OLLAMA_TIMEOUT"] = "30"
os.environ["ADAM_OLLAMA_RETRY_COUNT"] = "1"

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


async def start_mock_ollama():
    """يشغل mock Ollama في background."""
    print("Starting mock Ollama...")
    proc = subprocess.Popen(
        [sys.executable, str(Path(__file__).parent / "mock_ollama.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # ننتظره يبقى جاهز
    import httpx
    for _ in range(30):
        try:
            r = httpx.get("http://localhost:11434/api/tags", timeout=1.0)
            if r.status_code == 200:
                print("✅ Mock Ollama ready")
                return proc
        except Exception:
            pass
        await asyncio.sleep(0.5)
    print("❌ Mock Ollama failed to start")
    return proc


async def test_engine():
    """اختبار المحرك."""
    print("\n" + "=" * 60)
    print("1. Engine Tests")
    print("=" * 60)

    from adam.engine import AdamEngine, EngineConfig

    config = EngineConfig.from_env()
    engine = AdamEngine(config)

    passed = 0
    failed = 0

    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  ✅ {name}")
        else:
            failed += 1
            print(f"  ❌ {name} — {detail}")

    # 1.1 Init
    print("\n─── 1.1 Init ───")
    check("Engine created", engine is not None)
    check("SessionManager ready", engine.session_manager._conn is not None)
    check("MemoryStore ready", engine.memory._conn is not None)
    check("ToolDispatcher ready", engine.tools is not None)
    check("ContextCompressor ready", engine.compressor is not None)

    # 1.2 Model detection
    print("\n─── 1.2 Model Detection ───")
    models = await engine._detect_available_models()
    check("Detects available models", len(models) >= 3, f"models={models}")
    check("gemma4:12b detected", "gemma4:12b" in models)
    check("qwen2.5:0.5b detected", "qwen2.5:0.5b" in models)
    check("nomic-embed-text detected", "nomic-embed-text" in models)

    # 1.3 _call_ollama - qwen2.5:0.5b (بيشتغل)
    print("\n─── 1.3 _call_ollama (qwen2.5:0.5b) ───")
    messages = [
        {"role": "system", "content": "أنت آدم."},
        {"role": "user", "content": "مرحبا"},
    ]
    result = await engine._call_ollama(messages, model="qwen2.5:0.5b", timeout=10.0)
    check("qwen2.5:0.5b returns response", result is not None and len(result) > 0, f"result={result}")

    # 1.4 _call_ollama - gemma4:12b (thinking field)
    print("\n─── 1.4 _call_ollama (gemma4:12b - thinking) ───")
    result = await engine._call_ollama(messages, model="gemma4:12b", timeout=10.0)
    check("gemma4:12b returns response (from thinking)", result is not None and len(result) > 0, f"result={result}")

    # 1.5 Chat - fallback chain
    print("\n─── 1.5 Chat (fallback chain) ───")
    result = await engine.chat("مرحبا يا آدم")
    check("Chat returns response", bool(result.get("response")))
    check("Chat returns session_id", bool(result.get("session_id")))
    check("Chat backend is not mock", result.get("backend") != "mock", f"backend={result.get('backend')}")
    check("Chat returns model used", bool(result.get("backend")))
    print(f"     backend={result.get('backend')}")

    # 1.6 Stats
    print("\n─── 1.6 Stats ───")
    stats = engine.get_stats()
    check("Stats has engine_ready", "engine_ready" in stats)
    check("Stats has engine_type", stats.get("engine_type") == "integrated")
    check("Stats has available_models", len(stats.get("available_models", [])) >= 3)
    check("Stats has active_model", bool(stats.get("active_model")))
    check("Stats tracks primary_calls", stats.get("primary_calls", 0) > 0)
    print(f"     stats={json.dumps({k: v for k, v in stats.items() if k != 'available_models'}, indent=2)}")

    # 1.7 Health check
    print("\n─── 1.7 Health Check ───")
    health = await engine.health_check()
    check("Health returns status", "status" in health)
    check("Health has engine_ready", "engine_ready" in health)
    check("Health has services", "services" in health)
    check("Health engine_ready is True", health.get("engine_ready") is True, f"health={health}")
    check("Health detects ollama", health.get("services", {}).get("ollama") is True)
    check("Health detects primary_model", health.get("services", {}).get("primary_model") is True)
    print(f"     health={json.dumps(health, indent=2, default=str)}")

    # 1.8 Heal
    print("\n─── 1.8 Heal (auto-repair) ───")
    heal_result = await engine.heal()
    check("Heal returns results", "checked" in heal_result)
    check("Heal checks ollama", any("ollama" in s for s in heal_result.get("checked", [])))
    check("Heal checks memory", any("memory" in s for s in heal_result.get("checked", [])))
    check("Heal checks session_db", any("session_db" in s for s in heal_result.get("checked", [])))
    print(f"     heal={heal_result}")

    # 1.9 Memory store + recall
    print("\n─── 1.9 Memory (LTM) ───")
    mem_id = await engine.memory.store("test memory for adam", type="semantic", priority=3)
    check("Store memory", mem_id is not None)

    results = await engine.memory.search("test")
    check("Search memory", len(results) >= 1)

    recall = await engine.memory.recall_for_context("test")
    check("Recall for context", len(recall) > 0)

    # 1.10 Tools
    print("\n─── 1.10 Tools ───")
    tools = engine.tools.list_tools()
    check("List tools", len(tools) >= 10)

    r = await engine.tools.execute("disk_space", {})
    check("Tool: disk_space", r.success)

    r = await engine.tools.execute("shell", {"command": "echo test"})
    check("Tool: shell", r.success)

    r = await engine.tools.execute("shell", {"command": "rm -rf /"})
    check("Tool: shell (blocked)", not r.success)

    r = await engine.tools.execute("file_write", {"path": "/tmp/adam_test.txt", "content": "hello"})
    check("Tool: file_write", r.success)

    r = await engine.tools.execute("file_read", {"path": "/tmp/adam_test.txt"})
    check("Tool: file_read", r.success and "hello" in r.result.get("content", ""))

    # 1.11 Context compressor
    print("\n─── 1.11 Context Compressor ───")
    # اضبط threshold عشان نوصل للضغط بسهولة في الاختبار
    engine.compressor.usable = 800  # صغير عشان يضغط
    engine.compressor.threshold = 0.2
    long_msgs = [{"role": "system", "content": "أنت آدم. أنت التوأم الرقمي."}]
    for i in range(30):
        long_msgs.append({"role": "user", "content": f"Q{i} " + "x" * 100})
        long_msgs.append({"role": "assistant", "content": f"A{i} " + "y" * 100})

    compressed, comp_stats = await engine.compressor.compress(long_msgs)
    check("Compressor compresses", comp_stats.get("compressed"), f"stats={comp_stats}")
    check("Compressor saves tokens",
          comp_stats.get("compressed_tokens", 0) < comp_stats.get("original_tokens", 0),
          f"orig={comp_stats.get('original_tokens')} comp={comp_stats.get('compressed_tokens')}")
    check("Compressor protects system",
          any(m["role"] == "system" and "آدم" in m.get("content", "") for m in compressed))

    await engine.cleanup()
    print(f"\n  Engine: {passed} passed, {failed} failed")
    return failed == 0


async def test_api():
    """اختبار الـ API server."""
    print("\n" + "=" * 60)
    print("2. API Server Tests")
    print("=" * 60)

    from adam.engine import AdamEngine, EngineConfig, get_engine, cleanup_engine
    import adam.api.server_minimal as server_module

    # إعداد الـ engine
    config = EngineConfig.from_env()
    server_module._engine = AdamEngine(config)

    from fastapi.testclient import TestClient
    from adam.api.server_minimal import app

    client = TestClient(app)

    passed = 0
    failed = 0

    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  ✅ {name}")
        else:
            failed += 1
            print(f"  ❌ {name} — {detail}")

    # 2.1 /api/status — engine_ready
    print("\n─── 2.1 /api/status ───")
    r = client.get("/api/status")
    data = r.json()
    check("GET /api/status", r.status_code == 200)
    check("engine_ready is boolean", isinstance(data.get("engine_ready"), bool))
    check("engine_type is integrated", data.get("engine_type") == "integrated")
    print(f"     engine_ready={data.get('engine_ready')}, engine_type={data.get('engine_type')}")

    # 2.2 /api/engine/health
    print("\n─── 2.2 /api/engine/health ───")
    r = client.get("/api/engine/health")
    data = r.json()
    check("GET /api/engine/health", r.status_code == 200)
    check("Has services", "services" in data)
    check("Has engine_ready", "engine_ready" in data)
    check("Ollama detected", data.get("services", {}).get("ollama") is True)
    check("primary_model detected", data.get("services", {}).get("primary_model") is True)
    print(f"     status={data.get('status')}, engine_ready={data.get('engine_ready')}")

    # 2.3 /api/engine/diagnostics
    print("\n─── 2.3 /api/engine/diagnostics ───")
    r = client.get("/api/engine/diagnostics")
    data = r.json()
    check("GET /api/engine/diagnostics", r.status_code == 200)
    check("Has summary", "summary" in data)
    check("Has services", "services" in data)
    check("Has stats", "stats" in data)
    check("Has available_models", "available_models" in data)
    print(f"     summary={data.get('summary')}")

    # 2.4 /api/engine/heal
    print("\n─── 2.4 /api/engine/heal ───")
    r = client.post("/api/engine/heal")
    data = r.json()
    check("POST /api/engine/heal", r.status_code == 200)
    check("Has details", "details" in data)
    check("Heal checks ollama", "ollama" in str(data.get("details", {})))
    print(f"     status={data.get('status')}, details={data.get('details')}")

    # 2.5 /api/chat
    print("\n─── 2.5 /api/chat ───")
    r = client.post("/api/chat", json={"message": "مرحبا"})
    data = r.json()
    check("POST /api/chat", r.status_code == 200)
    check("Returns response", bool(data.get("response")))
    check("Returns session_id", bool(data.get("session_id")))
    check("Backend is not mock", data.get("backend") != "mock", f"backend={data.get('backend')}")
    print(f"     backend={data.get('backend')}, response={data.get('response', '')[:60]}")

    # 2.6 /api/chat/upload
    print("\n─── 2.6 /api/chat/upload ───")
    # أنشئ ملف test
    test_file = Path("/tmp/adam_upload_test.txt")
    test_file.write_text("هذا ملف اختبار لمحمد")

    with open(test_file, "rb") as f:
        r = client.post("/api/chat/upload", files={"file": ("test.txt", f, "text/plain")})
    data = r.json()
    check("POST /api/chat/upload", r.status_code == 200)
    check("Returns filename", bool(data.get("filename")))
    check("Returns text_content", bool(data.get("text_content")))
    check("Returns type", data.get("type") == "text")
    check("Content matches", "محمد" in data.get("text_content", ""))

    # 2.7 /api/chat/upload with session_id
    print("\n─── 2.7 /api/chat/upload with session_id ───")
    # أنشئ session الأول
    r = client.post("/api/chat", json={"message": "test"})
    session_id = r.json().get("session_id")

    with open(test_file, "rb") as f:
        r = client.post(
            "/api/chat/upload",
            files={"file": ("test2.txt", f, "text/plain")},
            params={"session_id": session_id},
        )
    data = r.json()
    check("Upload with session", r.status_code == 200)
    check("session_attached", data.get("session_attached") is True, f"data={data}")

    # 2.8 /api/voice/transcribe (stub)
    print("\n─── 2.8 /api/voice/transcribe ───")
    # أنشئ ملف audio وهمي
    audio_file = Path("/tmp/adam_test_audio.wav")
    audio_file.write_bytes(b"fake audio data")

    with open(audio_file, "rb") as f:
        r = client.post(
            "/api/voice/transcribe",
            files={"file": ("test.wav", f, "audio/wav")},
        )
    data = r.json()
    check("POST /api/voice/transcribe", r.status_code == 200)
    check("Returns transcript field", "transcript" in data)

    # 2.9 /api/voice/synthesize
    print("\n─── 2.9 /api/voice/synthesize ───")
    r = client.post("/api/voice/synthesize", json={"text": "مرحبا"})
    check("POST /api/voice/synthesize", r.status_code == 200)

    # 2.10 /api/ollama/models
    print("\n─── 2.10 /api/ollama/models ───")
    r = client.get("/api/ollama/models")
    data = r.json()
    check("GET /api/ollama/models", r.status_code == 200)
    check("Returns models", len(data.get("models", [])) >= 3)
    print(f"     models={[m['name'] for m in data.get('models', [])]}")

    # 2.11 /api/tools/manifest
    print("\n─── 2.11 /api/tools/manifest ───")
    r = client.get("/api/tools/manifest")
    data = r.json()
    check("GET /api/tools/manifest", r.status_code == 200)
    check("Has tools", len(data.get("tools", {})) >= 10)

    # 2.12 /api/tools/action
    print("\n─── 2.12 /api/tools/action ───")
    r = client.post("/api/tools/action", json={"name": "disk_space", "arguments": {}})
    check("POST /api/tools/action (disk_space)", r.json().get("success"))

    # 2.13 /metrics
    print("\n─── 2.13 /metrics ───")
    r = client.get("/metrics")
    check("GET /metrics", r.status_code == 200)

    # 2.14 /healthz/live
    print("\n─── 2.14 /healthz/live ───")
    r = client.get("/healthz/live")
    check("GET /healthz/live", r.status_code == 200)

    await cleanup_engine()
    print(f"\n  API: {passed} passed, {failed} failed")
    return failed == 0


async def test_integration():
    """اختبار التكامل — workflow كامل."""
    print("\n" + "=" * 60)
    print("3. Integration Tests")
    print("=" * 60)

    from adam.engine import AdamEngine, EngineConfig
    import adam.api.server_minimal as server_module

    config = EngineConfig.from_env()
    server_module._engine = AdamEngine(config)

    from fastapi.testclient import TestClient
    from adam.api.server_minimal import app

    client = TestClient(app)

    passed = 0
    failed = 0

    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  ✅ {name}")
        else:
            failed += 1
            print(f"  ❌ {name} — {detail}")

    print("\n─── 3.1 Full Chat Workflow ───")
    # 1. chat
    r = client.post("/api/chat", json={"message": "مرحبا"})
    data = r.json()
    session_id = data.get("session_id")
    check("Chat creates session", bool(session_id))
    check("Chat returns real response (not mock)", data.get("backend") != "mock")
    print(f"     backend={data.get('backend')}, response='{data.get('response', '')[:50]}'")

    # 2. chat with file
    print("\n─── 3.2 Chat with File ───")
    test_file = Path("/tmp/adam_integration_test.txt")
    test_file.write_text("هذا محتوى ملف اختبار")

    with open(test_file, "rb") as f:
        r = client.post("/api/chat/upload", files={"file": ("test.txt", f, "text/plain")})
    upload_data = r.json()
    check("Upload succeeds", bool(upload_data.get("text_content")))
    check("Upload extracts content", "اختبار" in upload_data.get("text_content", ""))

    # 3. chat with file content in message
    file_content = upload_data.get("text_content", "")
    message_with_file = f"حلل هذا الملف:\n\n--- FILE: test.txt ---\n{file_content}\n--- END FILE ---"
    r = client.post("/api/chat", json={
        "message": message_with_file,
        "session_id": session_id,
        "context": {
            "attachments": [{
                "type": "file",
                "name": "test.txt",
                "content": file_content,
            }],
        },
    })
    data = r.json()
    check("Chat with file content", bool(data.get("response")))
    check("Backend not mock", data.get("backend") != "mock")

    # 4. memory store + recall
    print("\n─── 3.3 Memory Workflow ───")
    r = client.post("/api/memory/store", json={"content": "اسم المستخدم محمد", "priority": 5})
    check("Store memory via API", r.json().get("success", False) if isinstance(r.json(), dict) else r.status_code == 200)

    r = client.get("/api/memory/search?query=محمد")
    data = r.json()
    check("Search memory via API", r.status_code == 200)

    # 5. diagnostics + heal
    print("\n─── 3.4 Diagnostics + Heal ───")
    r = client.get("/api/engine/diagnostics")
    data = r.json()
    check("Diagnostics shows services", "services" in data)
    check("Diagnostics shows engine_ready", "engine_ready" in data)

    r = client.post("/api/engine/heal")
    data = r.json()
    check("Heal returns results", "details" in data)
    check("Heal checks ollama", "ollama" in str(data.get("details", {})))

    # 6. stats
    print("\n─── 3.5 Stats ───")
    r = client.get("/api/engine/health")
    data = r.json()
    check("Health shows active_model", bool(data.get("model")))
    check("Health shows engine_ready", "engine_ready" in data)

    print(f"\n  Integration: {passed} passed, {failed} failed")
    return failed == 0


async def main():
    # تنظيف
    for f in ["/tmp/adam_test_final_sessions.db", "/tmp/adam_test_final_memory.db",
              "/tmp/adam_test_final_sessions.db-wal", "/tmp/adam_test_final_sessions.db-shm",
              "/tmp/adam_test_final_memory.db-wal", "/tmp/adam_test_final_memory.db-shm"]:
        try:
            os.unlink(f)
        except Exception:
            pass

    # ابدأ mock Ollama
    mock_proc = await start_mock_ollama()
    if not mock_proc:
        print("❌ Cannot start mock Ollama")
        return 1

    try:
        # شغل الاختبارات
        engine_ok = await test_engine()
        api_ok = await test_api()
        integration_ok = await test_integration()

        print("\n" + "=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        print(f"  Engine Tests:       {'✅ PASS' if engine_ok else '❌ FAIL'}")
        print(f"  API Tests:          {'✅ PASS' if api_ok else '❌ FAIL'}")
        print(f"  Integration Tests:  {'✅ PASS' if integration_ok else '❌ FAIL'}")
        print("=" * 60)

        if engine_ok and api_ok and integration_ok:
            print("\n🎉 كل الاختبارات نجحت!")
            return 0
        else:
            print("\n⚠️  فيه اختبارات فشلت. راجع التفاصيل فوق.")
            return 1
    finally:
        mock_proc.terminate()
        mock_proc.wait()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
