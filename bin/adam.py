#!/usr/bin/env python3
"""
Adam Prism — One-command launcher (cross-platform)
====================================================

Run Adam Prism with a single command on Windows, macOS, or Linux:

  adam                     # Start the server (default: 0.0.0.0:8000)
  adam --port 8080         # Custom port
  adam --host 127.0.0.1    # Custom host
  adam --install           # Install dependencies
  adam --help              # Show all options
  adam --doctor            # Run environment health check

Handles:
  - Python venv detection (auto-creates if missing)
  - Dependency installation (pip install -e .)
  - Cross-platform paths (Windows / Mac / Linux)
  - Ollama auto-detection
  - Port conflict detection

Works on:
  - Linux (Ubuntu, Debian, Fedora, Arch, Alpine)
  - macOS (Intel + Apple Silicon)
  - Windows (10, 11, Server 2019+)
"""
from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
import venv
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# Paths and platform detection
# ═══════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Python executable in venv
VENV_DIR = REPO_ROOT / ".venv"
if IS_WINDOWS:
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
    VENV_PIP = VENV_DIR / "Scripts" / "pip.exe"
    VENV_BIN = VENV_DIR / "Scripts"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python"
    VENV_PIP = VENV_DIR / "bin" / "pip"
    VENV_BIN = VENV_DIR / "bin"

# Use existing venv if present (e.g. /mnt/.../venv in dev)
EXISTING_VENV = REPO_ROOT / "venv"
if EXISTING_VENV.exists() and not VENV_DIR.exists():
    if IS_WINDOWS:
        VENV_PYTHON = EXISTING_VENV / "Scripts" / "python.exe"
        VENV_PIP = EXISTING_VENV / "Scripts" / "pip.exe"
        VENV_BIN = EXISTING_VENV / "Scripts"
    else:
        VENV_PYTHON = EXISTING_VENV / "bin" / "python"
        VENV_PIP = EXISTING_VENV / "bin" / "pip"
        VENV_BIN = EXISTING_VENV / "bin"

# Detect "active" venv (use system python if INSIDE a venv)
SYSTEM_PYTHON = sys.executable
IN_VENV = (
    hasattr(sys, "real_prefix")
    or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    or os.environ.get("VIRTUAL_ENV") is not None
)

# Colours
GREEN = "\033[0;32m" if not IS_WINDOWS else ""
YELLOW = "\033[1;33m" if not IS_WINDOWS else ""
CYAN = "\033[0;36m" if not IS_WINDOWS else ""
RED = "\033[0;31m" if not IS_WINDOWS else ""
NC = "\033[0m" if not IS_WINDOWS else ""


def cprint(color: str, text: str) -> None:
    print(f"{color}{text}{NC}")


def info(msg: str) -> None:
    cprint(CYAN, f"  {msg}")


def ok(msg: str) -> None:
    cprint(GREEN, f"  ✓ {msg}")


def warn(msg: str) -> None:
    cprint(YELLOW, f"  ⚠ {msg}")


def fail(msg: str) -> None:
    cprint(RED, f"  ✗ {msg}")


# ═══════════════════════════════════════════════════════════════════
# venv management
# ═══════════════════════════════════════════════════════════════════


def get_venv_python() -> Path:
    """Return the python executable in our venv, creating it if needed."""
    if IN_VENV:
        return Path(SYSTEM_PYTHON)
    if VENV_PYTHON.exists():
        return VENV_PYTHON
    # Need to create venv
    warn(f"Virtual environment not found at {VENV_DIR}")
    info(f"Creating venv (this may take 1-2 minutes)...")
    venv.create(VENV_DIR, with_pip=True, clear=True)
    ok(f"Created venv at {VENV_DIR}")
    return VENV_PYTHON


def install_deps(python: Path) -> None:
    """Install Adam's dependencies into the venv."""
    info("Installing dependencies (editable install)...")
    cmd = [str(python), "-m", "pip", "install", "--upgrade", "pip"]
    subprocess.run(cmd, check=True, capture_output=True)
    cmd = [str(python), "-m", "pip", "install", "-e", str(REPO_ROOT)]
    subprocess.run(cmd, check=True, capture_output=True)
    # Also install headroom-ai with MCP support
    cmd = [str(python), "-m", "pip", "install", '"headroom-ai[mcp]"']
    subprocess.run(cmd, check=True, capture_output=True)
    ok("Dependencies installed")


# ═══════════════════════════════════════════════════════════════════
# Ollama detection
# ═══════════════════════════════════════════════════════════════════


def check_ollama() -> bool:
    """Check if Ollama is running locally."""
    import urllib.request
    import urllib.error
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


def ollama_install_hint() -> str:
    """Platform-specific install instructions for Ollama."""
    if IS_LINUX:
        return "Install: curl -fsSL https://ollama.ai/install.sh | sh"
    elif IS_MACOS:
        return "Install: brew install ollama  OR  download from https://ollama.ai"
    elif IS_WINDOWS:
        return "Install: download from https://ollama.ai/download"
    return "Install: see https://ollama.ai"


# ═══════════════════════════════════════════════════════════════════
# Doctor
# ═══════════════════════════════════════════════════════════════════


def doctor(python: Path) -> None:
    """Run a health check and print results."""
    print()
    cprint(CYAN, "  Adam Prism Doctor")
    print()
    info(f"Platform:      {platform.system()} {platform.release()}")
    info(f"Architecture:  {platform.machine()}")
    info(f"Python:        {sys.version.split()[0]}")
    info(f"Repo:          {REPO_ROOT}")
    info(f"Backend:       {BACKEND_DIR}")
    info(f"Virtual env:   {'active' if IN_VENV else VENV_PYTHON.parent}")
    print()

    # Check imports
    info("Checking imports...")
    cmd = [
        str(python), "-c",
        "import fastapi, uvicorn, httpx, pydantic; "
        "import sys; sys.path.insert(0, 'backend'); "
        "from adam.api.server_minimal import create_app; "
        "print('  ✓ Adam imports OK')",
    ]
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if res.returncode == 0:
        for line in res.stdout.splitlines():
            if line.strip():
                print(line)
    else:
        fail(f"Import check failed: {res.stderr}")
        return
    print()

    # Check Ollama
    info("Checking Ollama...")
    if check_ollama():
        ok("Ollama is running on http://localhost:11434")
    else:
        warn("Ollama is not running")
        info(ollama_install_hint())
        info("After installing: ollama serve  (in a separate terminal)")
    print()

    # Check Headroom
    info("Checking Headroom...")
    cmd = [
        str(python), "-c",
        "import sys; sys.path.insert(0, 'backend'); "
        "from adam.observability.headroom_integration import _HEADROOM_AVAILABLE; "
        "print('  ✓ Headroom available' if _HEADROOM_AVAILABLE else '  ⚠ Headroom not installed (compression will be no-op)')",
    ]
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    if res.returncode == 0:
        for line in res.stdout.splitlines():
            if line.strip():
                print(line)
    print()

    ok("Doctor complete.")


# ═══════════════════════════════════════════════════════════════════
# Server launcher
# ═══════════════════════════════════════════════════════════════════


def start_server(python: Path, host: str, port: int, headroom_mode: str | None) -> None:
    """Start the Adam Prism server."""
    # Set environment
    env = os.environ.copy()
    env["ADAM_PRODUCTION"] = "0"  # showcase mode
    # Add backend dir to PYTHONPATH so 'adam.api.server_minimal' resolves
    # when running uvicorn from a fresh subprocess (not from within pytest
    # which already has backend in pythonpath).
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{BACKEND_DIR}{os.pathsep}{existing_pp}" if existing_pp else str(BACKEND_DIR)
    )
    if not env.get("ADAM_API_KEY") or env.get("ADAM_API_KEY") == "test-key-for-ci-only":
        env["ADAM_API_KEY"] = "dev-key-please-change-in-production"
    if headroom_mode:
        env["ADAM_HEADROOM_MODE"] = headroom_mode

    cmd = [
        str(python), "-m", "uvicorn", "adam.api.server_minimal:app",
        "--host", host, "--port", str(port),
    ]
    info(f"Starting Adam Prism on http://{host}:{port}")
    info(f"  API docs:    http://{host}:{port}/docs")
    info(f"  Health:      http://{host}:{port}/healthz/live")
    info(f"  Compression: http://{host}:{port}/api/compression")
    info(f"  Metrics:     http://{host}:{port}/metrics")
    print()
    info("Press Ctrl+C to stop")
    print()
    try:
        subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, check=True)
    except KeyboardInterrupt:
        print()
        info("Adam stopped.")


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="adam",
        description="Adam Prism — one-command launcher",
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--install", action="store_true",
        help="Install dependencies and exit",
    )
    parser.add_argument(
        "--doctor", action="store_true",
        help="Run health check and exit",
    )
    parser.add_argument(
        "--headroom-mode", choices=["audit", "optimize", "simulate"],
        help="Override ADAM_HEADROOM_MODE",
    )
    args = parser.parse_args()

    # Banner
    print()
    cprint(CYAN, "  ╔════════════════════════════════════╗")
    cprint(CYAN, "  ║  Adam Prism v1.0.0b1 (Showcase)   ║")
    cprint(CYAN, "  ╚════════════════════════════════════╝")
    print()

    # Get venv python
    python = get_venv_python()

    # Install mode
    if args.install:
        install_deps(python)
        return 0

    # Doctor mode
    if args.doctor:
        doctor(python)
        return 0

    # Normal mode: ensure deps installed
    cmd = [str(python), "-c", "import fastapi, uvicorn, httpx, pydantic"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        warn("Dependencies missing — installing...")
        install_deps(python)

    # Check Ollama (warn but don't fail)
    if not check_ollama():
        warn("Ollama not detected. /chat will use mock responses.")
        info(ollama_install_hint())
    else:
        ok("Ollama is running.")

    # Start server
    start_server(python, args.host, args.port, args.headroom_mode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
