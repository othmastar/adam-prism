"""
Adam Tools — Safe Tool Execution
=================================
12 أداة مع retry + timeout + safety.

Safety features:
- SSRF protection في browser_fetch
- Shell whitelist (blocks rm -rf /, shutdown, etc.)
- Python sandbox (no imports of os, sys, subprocess)
- Path validation (no /etc, /proc, ~/.ssh, etc.)
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import os
import re
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("adam_prism.tools")


# ============================================================
# Tool Result
# ============================================================

@dataclass
class ToolResult:
    success: bool
    result: Any = None
    error: str | None = None
    latency_ms: int = 0
    tool_name: str = ""


# ============================================================
# Safety Constants
# ============================================================

BLOCKED_COMMANDS = [
    "rm -rf /", "rm -rf /*", "shutdown", "reboot", "halt",
    "mkfs", "dd if=/dev/zero", "dd if=/dev/random",
    ":(){:|:&};:",  # fork bomb
    "chmod -R 777 /",
    ">", "/dev/sda",
]

SENSITIVE_PATHS = [
    "/etc", "/proc", "/sys", "/boot", "/dev",
    "/root", "/var/log",
]

BLOCKED_DOTFILES = [
    ".ssh", ".aws", ".config", ".env", ".gnupg",
    ".kube", ".docker", ".netrc", ".pgpass", ".htpasswd",
]

BLOCKED_FILENAMES = [
    "password", "credential", "secret", "token",
    "id_rsa", "id_ed25519",
]

BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "host.docker.internal"}


def is_safe_url(url: str) -> tuple[bool, str]:
    """SSRF protection — يتحقق إن الـ URL مش بيوصل لـ internal."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL"

    if parsed.scheme not in ("http", "https"):
        return False, f"Scheme not allowed: {parsed.scheme}"

    hostname = parsed.hostname or ""
    if not hostname:
        return False, "No hostname"

    if hostname.lower() in BLOCKED_HOSTS:
        return False, f"Blocked host: {hostname}"

    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_info:
            ip = sockaddr[0]
            try:
                ip_obj = ipaddress.ip_address(ip)
                # block private, loopback, link-local, cloud metadata
                if (ip_obj.is_private or ip_obj.is_loopback
                        or ip_obj.is_link_local or ip_obj.is_reserved):
                    return False, f"Private/loopback IP: {ip}"
                # cloud metadata
                if str(ip_obj) in ("169.254.169.254", "fd00:ec2::254"):
                    return False, f"Cloud metadata IP: {ip}"
            except ValueError:
                continue
    except socket.gaierror as e:
        return False, f"DNS resolution failed: {e}"

    return True, "ok"


def is_safe_path(path: str) -> tuple[bool, str]:
    """يتحقق من أمان المسار."""
    if not path:
        return False, "Empty path"

    try:
        abs_path = Path(path).expanduser().resolve()
    except Exception as e:
        return False, f"Invalid path: {e}"

    # block sensitive system paths
    for s in SENSITIVE_PATHS:
        if str(abs_path).startswith(s):
            return False, f"Sensitive path blocked: {s}"

    # block dotfiles
    for dot in BLOCKED_DOTFILES:
        if f"/{dot}/" in str(abs_path) or str(abs_path).endswith(f"/{dot}"):
            return False, f"Dotfile dir blocked: {dot}"

    # block sensitive filenames
    name_lower = abs_path.name.lower()
    for fn in BLOCKED_FILENAMES:
        if fn in name_lower:
            return False, f"Sensitive filename blocked: {fn}"

    return True, "ok"


def is_safe_command(command: str) -> tuple[bool, str]:
    """يتحقق من أمان أمر shell."""
    cmd_lower = command.lower().strip()
    for blocked in BLOCKED_COMMANDS:
        if blocked.lower() in cmd_lower:
            return False, f"Blocked command pattern: {blocked}"
    return True, "ok"


# ============================================================
# Tool Dispatcher
# ============================================================

class ToolDispatcher:
    """منفّذ الأدوات مع retry + timeout + safety."""

    def __init__(
        self,
        max_retries: int = 2,
        timeout: float = 30.0,
        memory_store=None,
    ):
        self.max_retries = max_retries
        self.timeout = timeout
        self.memory_store = memory_store
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(self.timeout))
        return self._client

    async def execute(self, tool_name: str, params: dict) -> ToolResult:
        """ينفذ أداة مع retry."""
        start = time.time()
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self._execute_once(tool_name, params),
                    timeout=self.timeout,
                )
                result.latency_ms = int((time.time() - start) * 1000)
                result.tool_name = tool_name
                return result
            except asyncio.TimeoutError:
                last_error = f"Tool timeout after {self.timeout}s"
                logger.warning(f"Tool {tool_name} timeout (attempt {attempt+1})")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Tool {tool_name} failed (attempt {attempt+1}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))

        return ToolResult(
            success=False,
            error=last_error,
            latency_ms=int((time.time() - start) * 1000),
            tool_name=tool_name,
        )

    async def _execute_once(self, tool_name: str, params: dict) -> ToolResult:
        """تنفيذ مرة واحدة."""

        # === Memory tools (LTM) ===
        if tool_name == "memory_store" and self.memory_store:
            content = params.get("content", "")
            mem_type = params.get("type", "semantic")
            priority = int(params.get("priority", 3))
            tags = params.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            mem_id = await self.memory_store.store(
                content=content, type=mem_type, priority=priority,
                tags=tags, source="tool"
            )
            return ToolResult(bool(mem_id), {"stored": bool(mem_id), "id": mem_id})

        if tool_name == "memory_recall" and self.memory_store:
            query = params.get("query", "")
            top_k = int(params.get("top_k", 5))
            results = await self.memory_store.search(query, top_k=top_k)
            return ToolResult(True, {
                "results": [
                    {
                        "content": r.memory.content,
                        "type": r.memory.type,
                        "score": round(r.score, 3),
                        "priority": r.memory.priority,
                    }
                    for r in results
                ],
                "total": len(results),
            })

        if tool_name == "search_knowledge" and self.memory_store:
            query = params.get("query", "")
            results = await self.memory_store.search(query, top_k=3)
            return ToolResult(True, {
                "results": [
                    {"content": r.memory.content, "score": round(r.score, 3)}
                    for r in results
                ]
            })

        # === File operations ===
        if tool_name == "file_read":
            path = params.get("path", "")
            safe, reason = is_safe_path(path)
            if not safe:
                return ToolResult(False, error=reason)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()[:10000]
                return ToolResult(True, {"content": content, "path": path})
            except Exception as e:
                return ToolResult(False, error=str(e))

        if tool_name == "file_write":
            path = params.get("path", "")
            content = params.get("content", "")
            safe, reason = is_safe_path(path)
            if not safe:
                return ToolResult(False, error=reason)
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return ToolResult(True, {"written": True, "bytes": len(content)})
            except Exception as e:
                return ToolResult(False, error=str(e))

        if tool_name == "file_download":
            url = params.get("url", "")
            save_path = params.get("save_path", "/tmp/adam_download")
            safe_url, reason = is_safe_url(url)
            if not safe_url:
                return ToolResult(False, error=reason)
            try:
                client = await self._get_client()
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                return ToolResult(True, {"saved": save_path, "bytes": len(resp.content)})
            except Exception as e:
                return ToolResult(False, error=str(e))

        # === Shell ===
        if tool_name == "shell":
            command = params.get("command", "")
            safe, reason = is_safe_command(command)
            if not safe:
                return ToolResult(False, error=reason)
            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True,
                    timeout=min(self.timeout, 30),
                )
                return ToolResult(
                    result.returncode == 0,
                    {
                        "stdout": result.stdout[:5000],
                        "stderr": result.stderr[:500],
                        "returncode": result.returncode,
                    },
                )
            except subprocess.TimeoutExpired:
                return ToolResult(False, error="Command timed out")
            except Exception as e:
                return ToolResult(False, error=str(e))

        # === Python exec (sandboxed) ===
        if tool_name == "python_exec":
            code = params.get("code", "")
            # sandbox checks
            if "__import__" in code:
                return ToolResult(False, error="__import__ not allowed")
            if re.search(r"\bimport\s+(os|sys|subprocess|shutil)\b", code):
                return ToolResult(False, error="import os/sys/subprocess not allowed")
            if "open(" in code and ("/etc" in code or "/proc" in code):
                return ToolResult(False, error="sensitive file access blocked")

            ALLOWED_BUILTINS = {
                "print", "range", "len", "int", "float", "str", "list",
                "dict", "tuple", "set", "bool", "type", "isinstance",
                "enumerate", "zip", "map", "filter", "sorted", "reversed",
                "min", "max", "sum", "abs", "round", "any", "all",
                "json", "re", "math",
            }
            try:
                output_buf = []
                def _print(*args, **kwargs):
                    output_buf.append(" ".join(str(a) for a in args))

                safe_builtins = {
                    k: __builtins__[k] if not isinstance(__builtins__, dict) else __builtins__.get(k)
                    for k in ALLOWED_BUILTINS
                    if (not isinstance(__builtins__, dict) and k in dir(__builtins__))
                    or (isinstance(__builtins__, dict) and k in __builtins__)
                }
                safe_builtins["print"] = _print
                # add modules
                import json as _json
                import re as _re
                import math as _math
                safe_builtins["json"] = _json
                safe_builtins["re"] = _re
                safe_builtins["math"] = _math

                local_ns = {}
                exec(code, {"__builtins__": safe_builtins}, local_ns)
                output = "\n".join(output_buf) if output_buf else "(no output)"
                return ToolResult(True, {"output": output[:5000]})
            except Exception as e:
                return ToolResult(False, error=f"Python error: {e}")

        # === System ===
        if tool_name == "disk_space":
            usage = shutil.disk_usage("/")
            return ToolResult(True, {
                "used_gb": usage.used // (1024**3),
                "free_gb": usage.free // (1024**3),
                "total_gb": usage.total // (1024**3),
                "percent": round(usage.used / usage.total * 100, 1),
            })

        # === Browser fetch (httpx-based, safe) ===
        if tool_name == "browser_fetch":
            url = params.get("url", "")
            safe, reason = is_safe_url(url)
            if not safe:
                return ToolResult(False, error=reason)
            try:
                client = await self._get_client()
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
                # strip HTML to text
                content = resp.text
                content = re.sub(r"<script.*?</script>", "", content, flags=re.DOTALL)
                content = re.sub(r"<style.*?</style>", "", content, flags=re.DOTALL)
                content = re.sub(r"<[^>]+>", " ", content)
                content = re.sub(r"\s+", " ", content).strip()
                return ToolResult(True, {"content": content[:10000], "url": url})
            except Exception as e:
                return ToolResult(False, error=str(e))

        if tool_name == "browser_open":
            url = params.get("url", "")
            safe, reason = is_safe_url(url)
            if not safe:
                return ToolResult(False, error=reason)
            # simulated — مش هنفتح متصفح حقيقي
            return ToolResult(True, {"url": url, "opened": "simulated"})

        if tool_name == "screenshot":
            return ToolResult(True, {"note": "screenshot not available in REST mode"})

        if tool_name == "tool_planning":
            return ToolResult(True, {"note": "planning is built-in"})

        # === Unknown ===
        return ToolResult(False, error=f"Unknown tool: {tool_name}")

    def list_tools(self) -> list[dict]:
        """يرجع قائمة الأدوات المتاحة."""
        return [
            {"name": "memory_store", "description": "حفظ معلومة في الذاكرة الدائمة",
             "parameters": {"content": "string", "type": "string", "priority": "int"}},
            {"name": "memory_recall", "description": "بحث في الذكريات (hybrid: BM25 + vector)",
             "parameters": {"query": "string", "top_k": "int"}},
            {"name": "search_knowledge", "description": "بحث معرفي",
             "parameters": {"query": "string"}},
            {"name": "file_read", "description": "قراءة ملف (مع safety)",
             "parameters": {"path": "string"}},
            {"name": "file_write", "description": "كتابة ملف (مع safety)",
             "parameters": {"path": "string", "content": "string"}},
            {"name": "file_download", "description": "تحميل ملف من URL (مع SSRF protection)",
             "parameters": {"url": "string", "save_path": "string"}},
            {"name": "shell", "description": "تنفيذ أمر (مع whitelist)",
             "parameters": {"command": "string"}},
            {"name": "python_exec", "description": "تنفيذ بايثون في sandbox",
             "parameters": {"code": "string"}},
            {"name": "disk_space", "description": "مساحة القرص",
             "parameters": {}},
            {"name": "browser_fetch", "description": "جلب محتوى URL (httpx + SSRF protection)",
             "parameters": {"url": "string"}},
            {"name": "browser_open", "description": "فتح URL (simulated)",
             "parameters": {"url": "string"}},
            {"name": "screenshot", "description": "لقطة شاشة (simulated)",
             "parameters": {}},
        ]

    async def cleanup(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
