"""
Adam Prism — Integration Tests
===============================
يختبر كل الـ enhancements اللي هتدمجها في مشروعك:
1. ContextCompressor
2. VectorMemory (hybrid search)
3. EnhancedBrowser (Playwright multi-tab)
4. MCPManager
5. IntegrationLayer
"""

import asyncio
import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# إعدادات اختبار
os.environ["ADAM_AUXILIARY_ENABLED"] = "false"
os.environ["LORA_SERVER_URL"] = "http://localhost:99999"
os.environ["ADAM_OLLAMA_URL"] = "http://localhost:99999"


async def test_context_compressor():
    print("\n" + "─" * 60)
    print("1. Context Compressor")
    print("─" * 60)

    from adam.enhancements.context_compressor import ContextCompressor, estimate_tokens

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

    comp = ContextCompressor(
        ollama_url="http://localhost:99999",
        auxiliary_model="qwen2.5:0.5b",
        max_context_tokens=2000,
        reserve_for_response=500,
        compression_threshold=0.3,
        protect_last_n=4,
    )
    check("Init", comp is not None)

    small = [
        {"role": "system", "content": "أنت آدم."},
        {"role": "user", "content": "مرحبا"},
    ]
    msgs, stats = await comp.compress(small)
    check("No compression for small", not stats["compressed"])

    large = [{"role": "system", "content": "أنت آدم. أنت التوأم الرقمي لمحمد عثمان."}]
    for i in range(30):
        large.append({"role": "user", "content": f"Question {i}: " + "x" * 100})
        large.append({"role": "assistant", "content": f"Answer {i}: " + "y" * 100})
    large.append({"role": "user", "content": "آخر سؤال"})

    msgs, stats = await comp.compress(large)
    check("Compresses large", stats["compressed"], f"stats={stats}")
    check("Uses fallback (no LLM)", stats.get("method") == "fallback")
    check("Saves tokens",
          stats.get("compressed_tokens", 0) < stats.get("original_tokens", 0))
    check("Protects system prompt",
          any(m["role"] == "system" and "آدم" in m.get("content", "") for m in msgs))

    tokens = estimate_tokens("hello world")
    check("Token estimation", tokens > 0)

    print(f"\n  Compressor: {passed} passed, {failed} failed")
    return failed == 0


async def test_vector_memory():
    print("\n" + "─" * 60)
    print("2. Vector Memory (Hybrid Search)")
    print("─" * 60)

    from adam.enhancements.vector_embeddings import VectorMemory, cosine_similarity, serialize_vector, deserialize_vector

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

    db_path = "/tmp/adam_test_vector.db"
    try:
        os.unlink(db_path)
    except Exception:
        pass

    vm = VectorMemory(
        db_path=db_path,
        ollama_url="http://localhost:99999",
        embedding_model="nomic-embed-text",
    )
    check("Init", vm._conn is not None)

    mid1 = await vm.store("اسم المستخدم محمد عثمان", type="semantic", priority=5, tags=["user"])
    check("Store memory 1", mid1 is not None)

    mid2 = await vm.store("المستخدم يفضل البرمجة بـ Python", type="preference", priority=4, tags=["programming"])
    check("Store memory 2", mid2 is not None)

    mid3 = await vm.store("Adam Prism مشروع ذكاء اصطناعي", type="semantic", priority=3)
    check("Store memory 3", mid3 is not None)

    mid_dup = await vm.store("اسم المستخدم محمد عثمان", type="semantic", priority=5)
    check("Duplicate returns same ID", mid_dup == mid1)

    results = await vm.search("محمد", top_k=5)
    check("Search finds results", len(results) >= 1)
    check("Search finds محمد", any("محمد" in r.memory.content for r in results))

    results = await vm.search("Python", top_k=5)
    check("Search finds Python", any("Python" in r.memory.content for r in results))

    context = await vm.recall_for_context("محمد", max_memories=3)
    check("Recall returns text", len(context) > 0)
    check("Recall has محمد", "محمد" in context)

    stats = vm.stats()
    check("Stats available", stats["available"])
    check("Stats total", stats["total"] >= 3)

    sim = cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    check("Cosine sim identical", abs(sim - 1.0) < 0.01)

    sim2 = cosine_similarity([1.0, 0.0], [0.0, 1.0])
    check("Cosine sim orthogonal", abs(sim2) < 0.01)

    vec = [1.0, 2.0, 3.0, 4.0]
    s = serialize_vector(vec)
    d = deserialize_vector(s)
    check("Serialize/deserialize", d == vec)

    ok = await vm.delete(mid3)
    check("Delete", ok)

    vm.close()
    try:
        os.unlink(db_path)
    except Exception:
        pass

    print(f"\n  VectorMemory: {passed} passed, {failed} failed")
    return failed == 0


async def test_enhanced_browser():
    print("\n" + "─" * 60)
    print("3. Enhanced Browser (Playwright Multi-tab)")
    print("─" * 60)

    from adam.enhancements.enhanced_browser import EnhancedBrowser, is_safe_url

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

    safe, _ = is_safe_url("https://example.com")
    check("SSRF: example.com safe", safe)

    safe, _ = is_safe_url("http://localhost/admin")
    check("SSRF: localhost blocked", not safe)

    safe, _ = is_safe_url("http://127.0.0.1/")
    check("SSRF: 127.0.0.1 blocked", not safe)

    safe, _ = is_safe_url("http://10.0.0.1/")
    check("SSRF: 10.x blocked", not safe)

    safe, _ = is_safe_url("file:///tmp/test.html")
    check("file:// allowed", safe)

    safe, _ = is_safe_url("ftp://example.com")
    check("FTP blocked", not safe)

    browser = EnhancedBrowser(headless=True, browser_type="chromium", max_pages=3)
    ok = await browser.init()
    if not ok:
        check("Browser init", False, "Playwright not available")
        print(f"\n  Browser: {passed} passed, {failed} failed")
        return failed == 0

    check("Init", ok)

    test_html = "<html><head><title>Adam Test</title></head><body><h1>Hello Adam</h1><p>This is a test</p><a href='#'>link1</a></body></html>"
    Path("/tmp/adam_browser_test.html").write_text(test_html)

    page_id = await browser.open("file:///tmp/adam_browser_test.html")
    check("Open page", page_id is not None, f"page_id={page_id}")

    if page_id:
        result = await browser.read_page(page_id)
        check("Read page", result["success"])
        check("Page has content", "Hello Adam" in result.get("text", ""))

        text = await browser.get_text(page_id)
        check("Get text", "Hello Adam" in text)

        links = await browser.get_links(page_id)
        check("Get links", len(links) >= 1)

        page_id2 = await browser.open("file:///tmp/adam_browser_test.html")
        check("Multi-tab: open second", page_id2 is not None and page_id2 != page_id)

        pages = browser.list_pages()
        check("Multi-tab: list 2 pages", len(pages) == 2)

        ss = await browser.screenshot(page_id, full_page=True)
        check("Screenshot", ss["success"])
        check("Screenshot base64", len(ss.get("base64", "")) > 100)
        check("Screenshot size", ss.get("size_bytes", 0) > 1000)

        js_result = await browser.execute_js(page_id, "1 + 1")
        check("Execute JS", js_result["success"] and js_result.get("result") == 2)

        click_result = await browser.click(page_id, "a")
        check("Click element", click_result["success"])

        closed = await browser.close_page(page_id2)
        check("Close page", closed)

        pages = browser.list_pages()
        check("Page count after close", len(pages) == 1)

    health = await browser.health_check()
    check("Health check", health)

    stats = browser.get_stats()
    check("Stats", stats["browser_type"] == "chromium")

    await browser.close()

    try:
        os.unlink("/tmp/adam_browser_test.html")
    except Exception:
        pass

    print(f"\n  Browser: {passed} passed, {failed} failed")
    return failed == 0


async def test_mcp_manager():
    print("\n" + "─" * 60)
    print("4. MCP Manager")
    print("─" * 60)

    from adam.enhancements.mcp_integration import MCPManager

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

    mcp = MCPManager(max_servers=5)
    ok = await mcp.init()
    if not ok:
        check("MCP init (mcp library not installed)", False,
              "Install with: pip install mcp")
        check("MCP available flag", not mcp.available)
        check("MCP health when unavailable", not mcp.health()["available"])

        result = await mcp.add_server("test", "npx", ["-y", "@modelcontextprotocol/server-filesystem"])
        check("Add server fails when unavailable", not result)

        print(f"\n  MCP: {passed} passed, {failed} failed")
        return failed == 0

    check("Init", ok)
    check("MCP available", mcp.available)

    health = mcp.health()
    check("Health (no servers)", health["servers_count"] == 0)

    servers = mcp.list_servers()
    check("List servers (empty)", len(servers) == 0)

    tools = mcp.list_tools()
    check("List tools (empty)", len(tools) == 0)

    result = await mcp.execute_tool("nonexistent", {})
    check("Execute unknown tool fails", not result["success"])

    await mcp.cleanup()
    check("Cleanup", True)

    print(f"\n  MCP: {passed} passed, {failed} failed")
    return failed == 0


async def test_integration_layer():
    print("\n" + "─" * 60)
    print("5. Integration Layer (الترابط)")
    print("─" * 60)

    from adam.enhancements.integration import IntegrationLayer

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

    config = {
        "ollama_base": "http://localhost:99999",
        "auxiliary_model": "qwen2.5:0.5b",
        "embedding_model": "nomic-embed-text",
        "context_window": 2000,
        "vector_memory_db": "/tmp/adam_integration_test.db",
        "browser_enabled": True,
        "browser_headless": True,
        "browser_type": "chromium",
    }

    try:
        os.unlink("/tmp/adam_integration_test.db")
    except Exception:
        pass

    integration = IntegrationLayer(config)
    await integration.init()

    check("Init", integration._initialized)
    check("Compressor ready", integration.compressor is not None)
    check("VectorMemory ready", integration.vector_memory._conn is not None)
    check("MCP ready", integration.mcp is not None)

    large_msgs = [{"role": "system", "content": "أنت آدم."}]
    for i in range(20):
        large_msgs.append({"role": "user", "content": f"Q{i} " + "x" * 100})
        large_msgs.append({"role": "assistant", "content": f"A{i} " + "y" * 100})

    compressed, stats = await integration.compress_context(large_msgs)
    check("Compress context", stats.get("compressed"))

    mid = await integration.store_memory("test integration memory", priority=3)
    check("Store memory", mid is not None)

    recall = await integration.recall_memory("test")
    check("Recall memory", len(recall) > 0)

    results = await integration.search_memory("test")
    check("Search memory", len(results) >= 1)

    if integration.browser:
        Path("/tmp/adam_integration_test.html").write_text(
            "<html><body><h1>Integration Test</h1></body></html>"
        )
        result = await integration.browser_open("file:///tmp/adam_integration_test.html")
        check("Browser open", result.get("success"), str(result))

        if result.get("success"):
            pages = integration.browser_list_pages()
            check("Browser list pages", len(pages) >= 1)
    else:
        check("Browser (not available)", False, "Playwright not installed")

    mcp_health = integration.mcp.health()
    check("MCP health", "available" in mcp_health)

    health = await integration.health_check()
    check("Health check", "compressor" in health)
    check("Health: vector_memory", "db_connected" in health["vector_memory"])
    check("Health: mcp", "available" in health["mcp"])

    stats = integration.stats()
    check("Stats", "vector_memory" in stats)
    check("Stats: mcp", "available" in stats["mcp"])

    servers = integration.mcp_list_servers()
    check("MCP list servers", isinstance(servers, list))

    tools = integration.mcp_list_tools()
    check("MCP list tools", isinstance(tools, list))

    await integration.cleanup()
    try:
        os.unlink("/tmp/adam_integration_test.db")
    except Exception:
        pass

    print(f"\n  Integration: {passed} passed, {failed} failed")
    return failed == 0


async def main():
    print("=" * 60)
    print("Adam Prism — Enhancements Test Suite")
    print("=" * 60)

    results = []
    results.append(await test_context_compressor())
    results.append(await test_vector_memory())
    results.append(await test_enhanced_browser())
    results.append(await test_mcp_manager())
    results.append(await test_integration_layer())

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    names = ["Context Compressor", "Vector Memory", "Enhanced Browser", "MCP Manager", "Integration Layer"]
    for name, ok in zip(names, results):
        print(f"  {name:25s}: {'✅ PASS' if ok else '❌ FAIL'}")
    print("=" * 60)

    if all(results):
        print("\n🎉 كل الـ enhancements شغّالة!")
        return 0
    else:
        print("\n⚠️  فيه enhancements فشلت. راجع التفاصيل فوق.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
