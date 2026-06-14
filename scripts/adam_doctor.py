#!/usr/bin/env python3
"""
[PHASE3] adam-doctor — Diagnose installation issues.

Checks:
- Python version
- Required Python packages
- Ollama running + models
- Qdrant running
- API server reachable
- Configuration valid
- Health endpoints responding

Exit codes:
  0 = all checks pass
  1 = warnings (some non-critical issues)
  2 = critical failure (cannot run Adam Prism)
"""
import asyncio
import os
import sys
import shutil

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
NC = "\033[0m"

def ok(msg: str) -> None:
    print(f"  {GREEN}✓{NC} {msg}")

def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{NC} {msg}")

def fail(msg: str) -> None:
    print(f"  {RED}✗{NC} {msg}")

def section(title: str) -> None:
    print(f"\n{BLUE}── {title} ──{NC}")

async def check_python() -> bool:
    section("Python")
    v = sys.version_info
    if v.major >= 3 and v.minor >= 10:
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
        return True
    fail(f"Python {v.major}.{v.minor} — need 3.10+")
    return False

def check_imports() -> bool:
    section("Python packages")
    all_ok = True
    required = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "httpx": "httpx",
        "pydantic": "Pydantic",
        "qdrant_client": "Qdrant client",
    }
    for mod, name in required.items():
        try:
            __import__(mod)
            ok(name)
        except ImportError:
            fail(f"{name} — run: pip install -e .")
            all_ok = False

    # Optional
    for mod, name in [
        ("jwt", "PyJWT"),
        ("bcrypt", "bcrypt"),
        ("redis", "Redis client"),
        ("sqlalchemy", "SQLAlchemy"),
    ]:
        try:
            __import__(mod)
            ok(f"{name} (optional)")
        except ImportError:
            warn(f"{name} (optional) — install for production features")
    return all_ok

def check_ollama() -> bool:
    section("Ollama")
    if not shutil.which("ollama"):
        fail("ollama CLI not found")
        print(f"    {BLUE}→{NC} Install: https://ollama.com/download")
        return False
    ok("ollama CLI installed")
    # Check if running
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        if req.status == 200:
            import json
            data = json.loads(req.read())
            models = [m.get("name") for m in data.get("models", [])]
            ok(f"Ollama running on port 11434 ({len(models)} models)")
            for m in models[:5]:
                print(f"    • {m}")
            if not models:
                warn("No models installed. Run: ollama pull gemma3:8b")
            return True
    except (urllib.error.URLError, ConnectionError, OSError):
        pass
    fail("Ollama not running on http://localhost:11434")
    print(f"    {BLUE}→{NC} Start: ollama serve (or brew services start ollama)")
    return False

def check_qdrant() -> bool:
    section("Qdrant")
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.urlopen("http://localhost:6333/", timeout=2)
        if req.status == 200:
            ok("Qdrant running on port 6333")
            return True
    except (urllib.error.URLError, ConnectionError, OSError):
        pass
    fail("Qdrant not running on http://localhost:6333")
    print(f"    {BLUE}→{NC} Start: docker run -d -p 6333:6333 qdrant/qdrant")
    return False

async def check_api(url: str = "http://localhost:8000") -> bool:
    section(f"Adam Prism API at {url}")
    import httpx
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            # Liveness
            r = await client.get(f"{url}/healthz/live")
            if r.status_code == 200:
                ok(f"Liveness probe: {r.json().get('status')}")
            else:
                fail(f"Liveness probe failed: HTTP {r.status_code}")
                return False
            # Readiness
            r = await client.get(f"{url}/healthz/ready")
            if r.status_code == 200:
                data = r.json()
                ok(f"Readiness probe: {data.get('status')}")
                for name, check in (data.get("checks") or {}).items():
                    healthy = check.get("healthy", False)
                    if healthy:
                        ok(f"  Subsystem {name}")
                    else:
                        warn(f"  Subsystem {name}: {check.get('error', 'unhealthy')}")
            else:
                warn(f"Readiness probe: HTTP {r.status_code} (engine still starting?)")
            # Status
            r = await client.get(f"{url}/api/status")
            if r.status_code == 200:
                data = r.json()
                ok(f"API status: {data.get('status')}")
                if "inference_mode" in data:
                    ok(f"Inference mode: {data['inference_mode']}")
                if "model" in data:
                    ok(f"Model: {data['model']}")
        return True
    except Exception as e:
        fail(f"API not reachable: {e}")
        print(f"    {BLUE}→{NC} Start: adam-prism --port 8000")
        return False

def check_config() -> bool:
    section("Configuration")
    if not os.path.exists(".env"):
        warn(".env not found — using defaults from config/default.json")
        return True
    ok(".env exists")
    # Check for default/insecure values
    with open(".env") as f:
        content = f.read()
    if "change-me-in-production" in content:
        fail("Default API key in .env — generate new: openssl rand -hex 32")
    else:
        ok("API key customized")
    if "admin-change-me" in content:
        warn("Default admin key in .env — should be changed")
    if "CHANGE-ME" in content:
        warn("Found CHANGE-ME placeholders — replace before production")
    if "ADAM_JWT_SECRET" not in content:
        warn("ADAM_JWT_SECRET not set — multi-user auth will use fallback")
    return True

def check_data_dir() -> bool:
    section("Data directory")
    data_dir = os.environ.get("ADAM_DATA_DIR", os.path.expanduser("~/.local/share/adam"))
    if not os.path.exists(data_dir):
        warn(f"Data directory doesn't exist: {data_dir}")
        print(f"    {BLUE}→{NC} Will be created on first run")
    else:
        ok(f"Data directory: {data_dir}")
        # Check disk space
        import shutil
        usage = shutil.disk_usage(data_dir)
        free_gb = usage.free / (1024 ** 3)
        if free_gb > 1.0:
            ok(f"{free_gb:.1f} GB free")
        else:
            fail(f"Only {free_gb:.1f} GB free — need at least 1GB")
    return True

async def main() -> int:
    print(f"\n{BLUE}╔════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║   Adam Prism — Doctor                  ║{NC}")
    print(f"{BLUE}╚════════════════════════════════════════╝{NC}")

    results: list[bool] = []
    results.append(check_python())
    results.append(check_imports())
    results.append(check_ollama())
    results.append(check_qdrant())
    results.append(check_config())
    results.append(check_data_dir())
    results.append(await check_api())

    # Summary
    passed = sum(results)
    total = len(results)
    print()
    if all(results):
        print(f"{GREEN}✅ All {total} checks passed!{NC}")
        print(f"{BLUE}→{NC} Start the API: adam-prism --port 8000")
        return 0
    elif passed >= total - 1:
        print(f"{YELLOW}⚠ {passed}/{total} checks passed (1 warning){NC}")
        return 1
    else:
        print(f"{RED}✗ {passed}/{total} checks passed{NC}")
        print(f"{YELLOW}Fix the issues above, then run adam-doctor again{NC}")
        return 2

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
