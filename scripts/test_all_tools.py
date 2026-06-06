"""اختبار شامل لكل الأدوات — كل أداة 3 مرات"""
import json, time, sys, os, asyncio
sys.path.insert(0, "/mnt/Workspace/Adam_Prism_Complete_v2")
from core.engine import AdamPrismEngine
from security.security_guard import TOOL_REGISTRY

CONFIG = {
    "inference_mode": "lora",
    "lora_server_url": "http://localhost:7860",
    "ollama_base": "http://localhost:11434",
    "model_name": "adam",
    "max_conversation_history": 10,
    "cycle_timeout": 120,
    "max_input_length": 8000,
    "max_tool_calls": 5,
    "tool_timeout": 30,
}

# كل أداة مع 3 مجموعات باراميتر (أو أقل لو الأداة بسيطة)
TOOL_TESTS = {
    # 🌐 Browser
    "browser_open":    [{"url": "https://example.com"}, {"url": "https://httpbin.org/get"}, {"url": "data:text/html,<h1>test</h1>"}],
    "browser_fetch":   [{"url": "https://example.com"}, {"url": "https://httpbin.org/get"}, {"url": "https://example.com"}],
    "browser_click":   [{"selector": "body"}, {"selector": "h1"}, {"selector": "a"}],
    "browser_type":    [{"text": "adam_test_1"}, {"text": "adam_test_2"}, {"text": "adam_test_3"}],
    "browser_read":    [{}, {}, {}],
    "screenshot":      [{}, {}, {}],
    # 🖱️ Mouse
    "mouse_click":     [{"button": "left"}, {"button": "right"}, {"x": 500, "y": 300}],
    "mouse_move":      [{"x": 100, "y": 100}, {"x": 200, "y": 200}, {"x": 500, "y": 500}],
    "mouse_scroll":    [{"delta_y": -100}, {"delta_y": 100}, {"delta_x": 50}],
    "mouse_drag":      [{"start_x": 100, "start_y": 100, "end_x": 200, "end_y": 200},
                        {"start_x": 200, "start_y": 200, "end_x": 300, "end_y": 300},
                        {"start_x": 50,  "start_y": 50,  "end_x": 150, "end_y": 150}],
    "mouse_position":  [{}, {}, {}],
    # ⌨️ Keyboard
    "keyboard_type":   [{"text": "test_1"}, {"text": "test_2"}, {"text": "test_3"}],
    "keyboard_press":  [{"key": "enter"}, {"key": "escape"}, {"key": "space"}],
    "keyboard_hotkey": [{"keys": ["ctrl", "c"]}, {"keys": ["ctrl", "v"]}, {"keys": ["alt", "tab"]}],
    # 📋 Clipboard
    "clipboard_read":  [{}, {}, {}],
    "clipboard_write": [{"text": "clip_test_1"}, {"text": "clip_test_2"}, {"text": "clip_test_3"}],
    # 🖥️ Screen
    "screen_ocr":      [{}, {}, {}],
    "screen_info":     [{}, {}, {}],
    # 📦 Window
    "window_focus":    [{"title": "RustDesk"}, {"title": "OpenCode"}, {"title": "RustDesk"}],
    "window_list":     [{}, {}, {}],
    # 📁 File
    "file_read":       [{"path": "/mnt/Workspace/adam_v8_output/AGENTS.md"},
                        {"path": "/mnt/Workspace/Adam_Prism_Complete_v2/core/engine.py"},
                        {"path": "/etc/hostname"}],
    "file_write":      [{"path": "/tmp/adam_test_1.txt", "content": "test_1"},
                        {"path": "/tmp/adam_test_2.txt", "content": "test_2"},
                        {"path": "/tmp/adam_test_3.txt", "content": "test_3"}],
    "file_download":   [{"url": "https://example.com"}, {"url": "https://httpbin.org/get"}, {"url": "https://example.com"}],
    "disk_space":      [{}, {}, {}],
    # 🧠 Knowledge
    "search_knowledge":[{"query": "test query", "top_k": 2},
                        {"query": "Qwen3.5", "top_k": 3},
                        {"query": "Adam agent", "top_k": 1}],
    # 📓 Notebook
    "notebook_update_profile": [{"section": "test", "data": {"k1": "v1"}},
                                {"section": "preferences", "data": {"lang": "ar"}},
                                {"section": "memory", "data": {"note": "test"}}],
    # ⚡ Execution
    "shell":           [{"command": "echo HELLO_ADAM_1"},
                        {"command": "pwd"},
                        {"command": "whoami"}],
    "python_exec":     [{"code": "print(2+2)"},
                        {"code": "import os; print(os.name)"},
                        {"code": "[x*2 for x in range(10)]"}],
}

async def test_all():
    print("🚀 Initializing engine...")
    engine = AdamPrismEngine(CONFIG)
    print("✅ Engine ready\n")

    results = {"pass": 0, "fail": 0, "skip": 0}
    # عدد الـ param sets لكل أداة
    counts = {}
    total_runs = 0

    for tool_name, param_sets in TOOL_TESTS.items():
        perm = TOOL_REGISTRY.get(tool_name)
        if not perm:
            print(f"  ⏭️  {tool_name}: مش موجود في TOOL_REGISTRY")
            results["skip"] += 1
            counts[tool_name] = 0
            continue

        counts[tool_name] = len(param_sets)
        for i, params in enumerate(param_sets):
            total_runs += 1
            tag = f"[{tool_name}#{i+1}/{len(param_sets)}]"
            try:
                t0 = time.time()
                result = await asyncio.wait_for(
                    engine._execute_tool(tool_name, params), timeout=25
                )
                dt = time.time() - t0
                success = result.get("success", False)
                status = "✅" if success else "❌"

                # Extract summary
                err = result.get("error", "")
                out = (result.get("output") or result.get("result") or result.get("data") or "")
                if isinstance(out, str) and len(out) > 100:
                    out = out[:100] + "..."

                print(f"  {status} {tag} ({dt:.1f}s)")
                if err:       print(f"     error: {err}")
                if out and success: print(f"     output: {out}")

                if success:
                    results["pass"] += 1
                else:
                    results["fail"] += 1

            except asyncio.TimeoutError:
                print(f"  ⏰ {tag} TIMEOUT")
                results["fail"] += 1
            except Exception as e:
                print(f"  💥 {tag} {e}")
                results["fail"] += 1

    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"  Total tools   : {len(TOOL_TESTS)}")
    print(f"  Total runs    : {total_runs}")
    print(f"  ✅ Passed     : {results['pass']}")
    print(f"  ❌ Failed     : {results['fail']}")
    print(f"  ⏭️  Skipped   : {results['skip']}")
    print(f"  Pass rate     : {results['pass']/(results['pass']+results['fail'])*100:.0f}%")
    print(f"{'='*60}")

    # Per-tool summary
    print(f"\n📋 Per-Tool Results:")
    for tool_name in TOOL_TESTS:
        n = counts.get(tool_name, 0)
        # Just show name and count
        print(f"  {tool_name}: {n} runs")

    return results

if __name__ == "__main__":
    results = asyncio.run(test_all())
    sys.exit(0 if results["fail"] == 0 else 1)
