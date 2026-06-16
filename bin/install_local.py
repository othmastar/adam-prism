#!/usr/bin/env python3
"""
Adam Prism — Python-only installer (cross-platform).

Installs Adam Prism and all its dependencies directly in your Python
environment. No Docker required. Works on Windows, macOS, and Linux.

Usage:
  python bin/install_local.py            # install
  python bin/install_local.py --dev      # install with dev deps
  python bin/install_local.py --check    # check installation
"""
from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
import venv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
IS_WINDOWS = platform.system() == "Windows"

# Create .venv inside repo (only if neither .venv nor venv exists)
EXISTING_VENV = REPO_ROOT / "venv"
VENV_DIR = REPO_ROOT / ".venv"
if EXISTING_VENV.exists():
    # Use the existing dev venv if it exists
    VENV_DIR = EXISTING_VENV
if IS_WINDOWS:
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
    VENV_PIP = VENV_DIR / "Scripts" / "pip.exe"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python"
    VENV_PIP = VENV_DIR / "bin" / "pip"


def info(msg: str) -> None:
    print(f"  → {msg}")


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def fail(msg: str) -> None:
    print(f"  ✗ {msg}", file=sys.stderr)
    sys.exit(1)


def header(msg: str) -> None:
    print()
    print(f"═══ {msg} ═══")
    print()


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kwargs)


def check_python() -> None:
    """Verify Python version is supported."""
    header("Checking Python")
    info(f"Python {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        fail("Python 3.10+ required")
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} OK")


def create_venv() -> None:
    """Create venv if missing."""
    if VENV_PYTHON.exists():
        info(f"venv already exists at {VENV_DIR}")
        return
    header("Creating virtual environment")
    info(f"Creating venv at {VENV_DIR} (1-2 minutes)...")
    venv.create(VENV_DIR, with_pip=True, clear=True)
    ok(f"Created venv at {VENV_DIR}")


def detect_existing_venv() -> Path | None:
    """Return the python executable if we're already inside a venv."""
    in_venv = (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        or os.environ.get("VIRTUAL_ENV") is not None
    )
    if in_venv:
        return Path(sys.executable)
    return None


def install_deps(dev: bool = False) -> None:
    """Install all dependencies into the venv."""
    header("Installing dependencies")

    # If we're already inside a venv, use it directly
    active_venv = detect_existing_venv()
    pip_cmd = [str(active_venv), "-m", "pip"] if active_venv else [str(VENV_PYTHON), "-m", "pip"]

    # Upgrade pip first
    info("Upgrading pip...")
    run([*pip_cmd, "install", "--upgrade", "pip", "wheel"], capture_output=True)

    # Install Adam in editable mode (reads pyproject.toml)
    info("Installing Adam Prism (editable)...")
    run([*pip_cmd, "install", "-e", str(REPO_ROOT)], capture_output=True)
    ok("Adam Prism installed")

    # Install headroom-ai (context compression)
    info("Installing headroom-ai[mcp] (context compression)...")
    try:
        run([*pip_cmd, "install", "headroom-ai[mcp]"], capture_output=True)
        ok("headroom-ai installed")
    except subprocess.CalledProcessError:
        info("headroom-ai install failed (non-fatal — compression will be a no-op)")

    # Optional dev deps
    if dev:
        info("Installing dev dependencies...")
        run([*pip_cmd, "install", "pytest", "ruff", "httpx"], capture_output=True)
        ok("dev dependencies installed")


def check_ollama() -> None:
    """Check if Ollama is running and warn if not."""
    header("Checking Ollama (optional)")
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        ok("Ollama is running on http://localhost:11434")
    except Exception:
        info("Ollama not detected. The /chat endpoint will use mock responses.")
        if platform.system() == "Linux":
            info("Install: curl -fsSL https://ollama.ai/install.sh | sh")
        elif platform.system() == "Darwin":
            info("Install: brew install ollama  OR  https://ollama.ai")
        else:
            info("Install: https://ollama.ai/download")


def verify() -> None:
    """Verify the installation works."""
    header("Verifying installation")
    # If we're already inside a venv, use it; otherwise use the venv python
    active_venv = detect_existing_venv()
    python = str(active_venv) if active_venv else str(VENV_PYTHON)
    code = (
        "import sys; sys.path.insert(0, 'backend'); "
        "from adam.api.server_minimal import create_app; "
        "app = create_app(); print(f'  ✓ Adam server ready with {len(app.routes)} routes')"
    )
    res = run([python, "-c", code], cwd=str(REPO_ROOT), capture_output=True, text=True)
    print(res.stdout.strip())
    if res.returncode != 0:
        fail("Verification failed")


def print_success() -> None:
    header("✓ Installation complete!")
    print("  Run Adam with one of these commands:")
    print()
    if IS_WINDOWS:
        print("    .\\bin\\adam")
    else:
        print("    ./bin/adam")
    print("    ./bin/adam --port 8080")
    print("    ./bin/adam --doctor")
    print()
    print("  Then open http://localhost:8000 in your browser.")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="install_local",
        description="Adam Prism Python-only installer (cross-platform)",
    )
    parser.add_argument(
        "--dev", action="store_true",
        help="Install dev dependencies (pytest, ruff, etc.)",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Check the installation without modifying anything",
    )
    parser.add_argument(
        "--no-ollama-check", action="store_true",
        help="Skip Ollama availability check",
    )
    args = parser.parse_args()

    print()
    print("  ╔════════════════════════════════════╗")
    print("  ║  Adam Prism Installer              ║")
    print("  ║  (Python-only, no Docker)         ║")
    print("  ╚════════════════════════════════════╝")
    print()
    info(f"Platform: {platform.system()} {platform.release()}")
    info(f"Repo: {REPO_ROOT}")

    if args.check:
        check_python()
        verify()
        if not args.no_ollama_check:
            check_ollama()
        return 0

    check_python()
    create_venv()
    install_deps(dev=args.dev)
    verify()
    if not args.no_ollama_check:
        check_ollama()
    print_success()
    return 0


if __name__ == "__main__":
    sys.exit(main())
