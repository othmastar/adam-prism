"""
Adam Prism — Complete E2E Test Suite
=====================================
يختبر كل المكونات والـ endpoints.
REST only — صفر WebSocket.
"""

import asyncio
import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# إعدادات اختبار (بدون LLMs حقيقية)
os.environ["ADAM_AUXILIARY_ENABLED"] = "false"
os.environ["LORA_SERVER_URL"] = "http://localhost:99999"
os.environ["ADAM_OLLAMA_URL"] = "http://localhost:99999"
os.environ["ADAM_SESSION_DB"] = "/tmp/adam_final_test_sessions.db"
os.environ["ADAM_MEMORY_DB"] = "/tmp/adam_final_test_memory.db"


async def test_engine():
    """اختبار المحرك."""
    print("=" * 60)
    print("1. Engine Tests")
    print("=" * 60)

    from adam_v3.engine import AdamEngine, EngineConfig

    config = EngineConfig.from_env()
    config.auxiliary_enabled = False
    engine = AdamEngine(config)

    tests_passed = 0
    tests_failed = 0

    def check(name, cond, detail=""):
        nonlocal tests_passed, tests_failed
        if cond:
            tests_passed += 1
            print(f"  ✅ {name}")
        else:
            tests_failed += 1
            print(f"  ❌ {name} — {detail}")

    # 1.1 Engine initialization
    print("\n─── 1.1 Engine Init ───")
    check("Engine created", engine is not None)
    check("SessionManager ready", engine.session_manager._conn is not None)
    check("MemoryStore ready", engine.memory._conn is not None)
    check("ToolDispatcher ready", engine.tools is not None)
    check("ContextCompressor ready", engine.compressor is not None)

    # 1.2 Health check
    print("\n─── 1.2 Health Check ───")
    health = await engine.health_check()
    check("Health check returns", "status" in health)
    check("Session DB service", health["services"].get("session_db") is True)
    check("Memory service", health["services"].get("memory") is True)

    # 1.3 Session management
    print("\n─── 1.3 Session Management ───")
    session_id = await engine.session_manager.create_session(user_id="test", model="gemma4-12b")
    check("Create session", session_id is not None, f"session_id={session_id}")

    msg_id = await engine.session_manager.add_message(session_id, "user", "test message")
    check("Add message", msg_id > 0)

    msgs = await engine.session_manager.get_messages(session_id)
    check("Get messages", len(msgs) == 1)

    sessions = await engine.session_manager.list_sessions(user_id="test")
    check("List sessions", len(sessions) >= 1)

    stats = await engine.session_manager.get_session_stats(session_id)
    check("Session stats", stats["message_count"] == 1)

    # 1.4 Memory store
    print("\n─── 1.4 Memory Store ───")
    mem_id = await engine.memory.store("test memory content", type="semantic", priority=3)
    check("Store memory", mem_id is not None)

    results = await engine.memory.search("test")
    check("Search memory", len(results) >= 1)

    mem_stats = engine.memory.stats()
    check("Memory stats", mem_stats["total"] >= 1)

    # 1.5 Tools
    print("\n─── 1.5 Tools ───")
    tools = engine.tools.list_tools()
    check("List tools", len(tools) >= 10)

    # disk_space
    result = await engine.tools.execute("disk_space", {})
    check("Tool: disk_space", result.success)

    # file_write + read
    result = await engine.tools.execute("file_write", {"path": "/tmp/adam_test.txt", "content": "hello"})
    check("Tool: file_write", result.success)

    result = await engine.tools.execute("file_read", {"path": "/tmp/adam_test.txt"})
    check("Tool: file_read", result.success and "hello" in result.result.get("content", ""))

    # shell (safe)
    result = await engine.tools.execute("shell", {"command": "echo test"})
    check("Tool: shell (safe)", result.success)

    # shell (blocked)
    result = await engine.tools.execute("shell", {"command": "rm -rf /"})
    check("Tool: shell (blocked)", not result.success)

    # python_exec
    result = await engine.tools.execute("python_exec", {"code": "print(2+3)"})
    check("Tool: python_exec", result.success and "5" in result.result.get("output", ""))

    # browser_fetch (SSRF blocked)
    result = await engine.tools.execute("browser_fetch", {"url": "http://localhost/admin"})
    check("Tool: browser_fetch (SSRF blocked)", not result.success and "SSRF" in result.error or "Blocked" in result.error or "Private" in result.error)

    # unknown tool
    result = await engine.tools.execute("unknown_tool", {})
    check("Tool: unknown (rejected)", not result.success)

    # 1.6 Context Compressor
    print("\n─── 1.6 Context Compressor ───")
    # اضغط threshold عشان نوصل للضغط بسهولة
    engine.compressor.threshold = 0.1
    engine.compressor.usable = 1000  # صغير عشان يضغط
    long_messages = [{"role": "system", "content": "أنت آدم."}]
    for i in range(30):
        long_messages.append({"role": "user", "content": f"Question {i}: " + "x" * 200})
        long_messages.append({"role": "assistant", "content": f"Answer {i}: " + "y" * 200})

    compressed, stats = await engine.compressor.compress(long_messages)
    check("Compressor compresses", stats.get("compressed", False),
          f"stats={stats}")
    check("Compressor saves tokens",
          stats.get("compressed_tokens", 0) < stats.get("original_tokens", 0),
          f"orig={stats.get('original_tokens')} comp={stats.get('compressed_tokens')}")
    check("Compressor protects system",
          any(m["role"] == "system" and "آدم" in m.get("content", "") for m in compressed))

    # 1.7 Chat (mock fallback)
    print("\n─── 1.7 Chat (Mock Fallback) ───")
    result = await engine.chat("مرحبا")
    check("Chat returns response", bool(result.get("response")))
    check("Chat returns session_id", bool(result.get("session_id")))
    check("Chat returns backend", result.get("backend") == "mock")

    await engine.cleanup()
    print(f"\nEngine Tests: {tests_passed} passed, {tests_failed} failed")
    return tests_failed == 0


async def test_api():
    """اختبار الـ API server."""
    print("\n" + "=" * 60)
    print("2. API Server Tests")
    print("=" * 60)

    from fastapi.testclient import TestClient
    from adam_v3.server import app

    client = TestClient(app)

    tests_passed = 0
    tests_failed = 0

    def check(name, cond, detail=""):
        nonlocal tests_passed, tests_failed
        if cond:
            tests_passed += 1
            print(f"  ✅ {name}")
        else:
            tests_failed += 1
            print(f"  ❌ {name} — {detail}")

    # 2.1 Basic endpoints
    print("\n─── 2.1 Basic Endpoints ───")
    r = client.get("/healthz/live")
    check("GET /healthz/live", r.status_code == 200)

    r = client.get("/api/status")
    check("GET /api/status", r.status_code == 200 and r.json().get("status") == "ok")

    r = client.get("/api/engine/health")
    check("GET /api/engine/health", r.status_code == 200 and "services" in r.json())

    r = client.get("/api/engine/diagnostics")
    check("GET /api/engine/diagnostics", r.status_code == 200 and "summary" in r.json())

    r = client.get("/metrics")
    check("GET /metrics", r.status_code == 200 and "adam_" in r.text)

    r = client.post("/api/engine/heal")
    check("POST /api/engine/heal", r.status_code == 200)

    r = client.get("/api/engine/pipeline-log")
    check("GET /api/engine/pipeline-log", r.status_code == 200)

    # 2.2 Chat
    print("\n─── 2.2 Chat ───")
    r = client.post("/api/chat", json={"message": "مرحبا"})
    data = r.json()
    check("POST /api/chat", r.status_code == 200 and "response" in data)
    check("Chat returns session_id", bool(data.get("session_id")))
    check("Chat returns mode", "mode" in data)
    check("Chat returns cycle", "cycle" in data)

    # 2.3 Sessions
    print("\n─── 2.3 Sessions ───")
    r = client.get("/api/chat/sessions")
    check("GET /api/chat/sessions", r.status_code == 200)

    r = client.post("/api/chat/sessions/test-session/sync", json=[
        {"role": "user", "content": "test"}
    ])
    check("POST /api/chat/sessions/{id}/sync", r.status_code == 200)

    r = client.post("/api/chat/sessions/test-session/messages", json={
        "role": "user", "content": "test"
    })
    check("POST /api/chat/sessions/{id}/messages", r.status_code == 200)

    r = client.post("/api/chat/search", json={"query": "test"})
    check("POST /api/chat/search", r.status_code == 200)

    # 2.4 Memory
    print("\n─── 2.4 Memory ───")
    r = client.post("/api/memory/store", json={
        "content": "test memory", "type": "semantic", "priority": 3
    })
    check("POST /api/memory/store", r.status_code == 200 and r.json()["success"])

    r = client.get("/api/memory/recall?query=test")
    check("GET /api/memory/recall", r.status_code == 200)

    r = client.get("/api/memory/stats")
    check("GET /api/memory/stats", r.status_code == 200)

    # 2.5 LTM
    print("\n─── 2.5 LTM (Long-term Memory) ───")
    r = client.post("/api/ltm/store", json={
        "content": "ltm test", "type": "semantic", "priority": 4
    })
    check("POST /api/ltm/store", r.status_code == 200)

    r = client.get("/api/ltm/search?query=test")
    check("GET /api/ltm/search", r.status_code == 200)

    r = client.get("/api/ltm/recall?query=test")
    check("GET /api/ltm/recall", r.status_code == 200)

    r = client.get("/api/ltm/stats")
    check("GET /api/ltm/stats", r.status_code == 200)

    r = client.get("/api/ltm/health")
    check("GET /api/ltm/health", r.status_code == 200)

    # 2.6 Knowledge (stubs)
    print("\n─── 2.6 Knowledge ───")
    r = client.post("/api/knowledge/search", json={"query": "test"})
    check("POST /api/knowledge/search", r.status_code == 200)

    r = client.post("/api/knowledge/add", json={"content": "test"})
    check("POST /api/knowledge/add", r.status_code == 200)

    r = client.get("/api/knowledge/collections")
    check("GET /api/knowledge/collections", r.status_code == 200)

    r = client.get("/api/knowledge/recent")
    check("GET /api/knowledge/recent", r.status_code == 200)

    # 2.7 Skills (stubs)
    print("\n─── 2.7 Skills ───")
    r = client.get("/api/skills/list")
    check("GET /api/skills/list", r.status_code == 200 and "skills" in r.json())

    r = client.get("/api/skills")
    check("GET /api/skills", r.status_code == 200)

    r = client.post("/api/skills/load", json={"skill_name": "test"})
    check("POST /api/skills/load", r.status_code == 200)

    # 2.8 Plugins (stubs)
    print("\n─── 2.8 Plugins ───")
    r = client.get("/api/plugins")
    check("GET /api/plugins", r.status_code == 200)

    r = client.get("/api/plugins/test")
    check("GET /api/plugins/{name}", r.status_code == 200)

    r = client.post("/api/plugins/load", json={"name": "test"})
    check("POST /api/plugins/load", r.status_code == 200)

    # 2.9 Subagents (stubs)
    print("\n─── 2.9 Subagents ───")
    r = client.get("/api/subagents")
    check("GET /api/subagents", r.status_code == 200)

    r = client.get("/api/subagents/test-id")
    check("GET /api/subagents/{id}", r.status_code == 200)

    r = client.post("/api/subagents/spawn", json={"type": "test"})
    check("POST /api/subagents/spawn", r.status_code == 200)

    # 2.10 Scheduler (stubs)
    print("\n─── 2.10 Scheduler ───")
    r = client.get("/api/scheduler/jobs")
    check("GET /api/scheduler/jobs", r.status_code == 200)

    r = client.get("/api/scheduler/jobs/test-id")
    check("GET /api/scheduler/jobs/{id}", r.status_code == 200)

    r = client.delete("/api/scheduler/jobs/test-id")
    check("DELETE /api/scheduler/jobs/{id}", r.status_code == 200)

    r = client.post("/api/scheduler/cron", json={"schedule": "0 * * * *"})
    check("POST /api/scheduler/cron", r.status_code == 200)

    r = client.post("/api/scheduler/interval", json={"seconds": 60})
    check("POST /api/scheduler/interval", r.status_code == 200)

    r = client.post("/api/scheduler/once", json={"delay": 60})
    check("POST /api/scheduler/once", r.status_code == 200)

    # 2.11 Notebook (stubs)
    print("\n─── 2.11 Notebook ───")
    r = client.get("/api/notebook/2026-06-24")
    check("GET /api/notebook/{date}", r.status_code == 200)

    r = client.get("/api/notebook/stats")
    check("GET /api/notebook/stats", r.status_code == 200)

    # 2.12 Security (stub)
    print("\n─── 2.12 Security ───")
    r = client.get("/api/security/stats")
    check("GET /api/security/stats", r.status_code == 200)

    # 2.13 Voice (stubs)
    print("\n─── 2.13 Voice ───")
    r = client.post("/api/voice/chat", json={"audio": "test"})
    check("POST /api/voice/chat", r.status_code == 200)

    # 2.14 Ollama
    print("\n─── 2.14 Ollama ───")
    r = client.get("/api/ollama/models")
    check("GET /api/ollama/models", r.status_code == 200)

    r = client.post("/api/ollama/select", json={"model": "qwen2.5:3b"})
    check("POST /api/ollama/select", r.status_code == 200)

    # 2.15 Settings + Auth
    print("\n─── 2.15 Settings + Auth ───")
    r = client.post("/api/settings/update", json={"settings": {"key": "value"}})
    check("POST /api/settings/update", r.status_code == 200)

    r = client.post("/api/auth/verify", json={"token": "test"})
    check("POST /api/auth/verify", r.status_code == 200)

    # 2.16 Pipeline
    print("\n─── 2.16 Pipeline ───")
    r = client.post("/api/pipeline/summarize", json={"text": "test text to summarize"})
    check("POST /api/pipeline/summarize", r.status_code == 200)

    # 2.17 Tools
    print("\n─── 2.17 Tools ───")
    r = client.get("/api/tools/manifest")
    check("GET /api/tools/manifest", r.status_code == 200 and "tools" in r.json())

    r = client.post("/api/tools/action", json={"name": "disk_space", "arguments": {}})
    check("POST /api/tools/action (disk_space)", r.json().get("success"))

    r = client.post("/api/tools/action", json={
        "action": {"type": "shell", "params": {"command": "echo test"}}
    })
    check("POST /api/tools/action (legacy format)", r.status_code == 200)

    # 2.18 JSON Mode
    print("\n─── 2.18 JSON Mode ───")
    r = client.post("/api/json-mode", json={
        "schema": {"name": "string"}, "query": "ما اسمك؟"
    })
    check("POST /api/json-mode", r.status_code == 200)

    # 2.19 WebSocket — يجب أن يرفض بنظافة
    print("\n─── 2.19 WebSocket (disabled) ───")
    try:
        with client.websocket_connect("/ws/chat") as ws:
            data = ws.receive_json()
            check("WebSocket rejected cleanly", data.get("type") == "error")
    except Exception as e:
        # WebSocketDisconnect هو السلوك الصحيح
        check("WebSocket rejected cleanly", True)

    print(f"\nAPI Tests: {tests_passed} passed, {tests_failed} failed")
    return tests_failed == 0


async def test_integration():
    """اختبار التكامل — workflow كامل."""
    print("\n" + "=" * 60)
    print("3. Integration Tests (Full Workflow)")
    print("=" * 60)

    from fastapi.testclient import TestClient
    from adam_v3.server import app

    client = TestClient(app)

    tests_passed = 0
    tests_failed = 0

    def check(name, cond, detail=""):
        nonlocal tests_passed, tests_failed
        if cond:
            tests_passed += 1
            print(f"  ✅ {name}")
        else:
            tests_failed += 1
            print(f"  ❌ {name} — {detail}")

    # Workflow: chat → store memory → recall → search

    print("\n─── 3.1 Chat + Memory Workflow ───")
    # 1. chat
    r = client.post("/api/chat", json={"message": "احفظ إن اسمي محمد"})
    data = r.json()
    session_id = data.get("session_id")
    check("Chat returns session", bool(session_id))

    # 2. store memory via API
    r = client.post("/api/memory/store", json={
        "content": "اسم المستخدم محمد", "type": "semantic", "priority": 5
    })
    check("Store memory via API", r.json()["success"])

    # 3. recall
    r = client.get("/api/memory/recall?query=محمد")
    data = r.json()
    check("Recall finds memory", data["total"] >= 1)

    # 4. LTM search
    r = client.get("/api/ltm/search?query=محمد")
    data = r.json()
    check("LTM search works", r.status_code == 200)

    # 5. stats reflect activity
    r = client.get("/api/memory/stats")
    stats = r.json()
    check("Stats reflect storage", stats.get("total", 0) >= 1)

    print("\n─── 3.2 Tool Execution Workflow ───")
    # write file via tool
    r = client.post("/api/tools/action", json={
        "name": "file_write",
        "arguments": {"path": "/tmp/adam_integration.txt", "content": "integration test"}
    })
    check("Tool: file_write", r.json()["success"])

    # read it back
    r = client.post("/api/tools/action", json={
        "name": "file_read",
        "arguments": {"path": "/tmp/adam_integration.txt"}
    })
    check("Tool: file_read", r.json()["success"])
    check("File content matches", "integration test" in r.json()["result"].get("content", ""))

    print("\n─── 3.3 Sessions Workflow ───")
    # create session
    r = client.post("/api/chat", json={"message": "test session"})
    session_id = r.json().get("session_id")
    check("Session created via chat", bool(session_id))

    # get session
    r = client.get(f"/api/chat/sessions/{session_id}")
    check("Get session", r.status_code == 200)

    # sync messages
    r = client.post(f"/api/chat/sessions/{session_id}/sync", json=[
        {"role": "user", "content": "synced message"}
    ])
    check("Sync messages", r.status_code == 200 and r.json()["synced"] == 1)

    # delete session
    r = client.delete(f"/api/chat/sessions/{session_id}")
    check("Delete session", r.status_code == 200)

    print(f"\nIntegration Tests: {tests_passed} passed, {tests_failed} failed")
    return tests_failed == 0


async def main():
    # cleanup
    for f in ["/tmp/adam_final_test_sessions.db", "/tmp/adam_final_test_memory.db",
              "/tmp/adam_final_test_sessions.db-wal", "/tmp/adam_final_test_sessions.db-shm",
              "/tmp/adam_final_test_memory.db-wal", "/tmp/adam_final_test_memory.db-shm"]:
        try:
            os.unlink(f)
        except Exception:
            pass

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
        print("\n🎉 كل الاختبارات نجحت! النظام جاهز للنشر.")
        return 0
    else:
        print("\n⚠️  فيه اختبارات فشلت. راجع التفاصيل فوق.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
