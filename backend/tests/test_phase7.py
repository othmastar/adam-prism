"""Tests for [PHASE7] additions: i18n, SSE limiter, backup CLI."""
from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import pytest


# ── i18n ──────────────────────────────────────────────────────────────────
class TestI18n:
    def test_translate_arabic_default(self, monkeypatch):
        monkeypatch.setenv("ADAM_LOCALE", "ar")
        from adam.i18n import t, set_locale, get_locale
        set_locale("ar")
        assert "أهلاً" in t("chat.welcome") or "آدم" in t("chat.welcome")
        assert get_locale() == "ar"

    def test_translate_english(self, monkeypatch):
        from adam.i18n import t, set_locale
        set_locale("en")
        msg = t("chat.welcome")
        assert "Adam" in msg
        assert "Welcome" in msg or "listening" in msg

    def test_translate_substitution(self):
        from adam.i18n import t, set_locale
        set_locale("en")
        msg = t("waf.blocked", reason="SQL injection")
        assert "SQL injection" in msg

    def test_translate_fallback_unknown_key(self):
        from adam.i18n import t
        assert t("nonexistent.key") == "nonexistent.key"

    def test_register_new_key(self):
        from adam.i18n import t, register, set_locale
        register("test.greeting", "أهلاً", "hello")
        set_locale("en")
        assert t("test.greeting") == "hello"
        set_locale("ar")
        assert t("test.greeting") == "أهلاً"

    def test_available_keys(self):
        from adam.i18n import available_keys
        keys = available_keys()
        assert "chat.welcome" in keys
        assert "waf.blocked" in keys
        assert "voice.cloned" in keys
        assert all("." in k for k in keys)


# ── SSE Limiter ──────────────────────────────────────────────────────────
class TestSSELimiter:
    def test_acquire_release(self):
        from adam.api.sse_limiter import SSERateLimiter
        lim = SSERateLimiter(max_concurrent_per_ip=2, max_concurrent_global=10)
        assert lim.acquire("client-1") is None
        assert lim.acquire("client-1") is None
        err = lim.acquire("client-1")
        assert err is not None and "too_many" in err
        lim.release("client-1")
        assert lim.acquire("client-1") is None

    def test_global_cap(self):
        from adam.api.sse_limiter import SSERateLimiter
        lim = SSERateLimiter(max_concurrent_per_ip=100, max_concurrent_global=3)
        assert lim.acquire("a") is None
        assert lim.acquire("b") is None
        assert lim.acquire("c") is None
        err = lim.acquire("d")
        assert err is not None and "server_busy" in err

    def test_token_rate_limit(self):
        from adam.api.sse_limiter import SSERateLimiter
        lim = SSERateLimiter(max_tokens_per_sec=10)
        lim.acquire("c1")
        # First small batch ok
        assert lim.record_tokens("c1", 5) is None
        # Big burst triggers (window resets on next second)
        err = lim.record_tokens("c1", 1000)
        assert err is not None and "token_rate" in err

    def test_byte_rate_limit(self):
        from adam.api.sse_limiter import SSERateLimiter
        lim = SSERateLimiter(max_bytes_per_sec=100)
        lim.acquire("c1")
        # First 50 bytes ok
        assert lim.record_bytes("c1", 50) is None
        # 1000 bytes triggers
        err = lim.record_bytes("c1", 1000)
        assert err is not None and "byte_rate" in err

    def test_idle_detection(self):
        import time
        from adam.api.sse_limiter import SSERateLimiter
        lim = SSERateLimiter(idle_timeout_sec=1)
        lim.acquire("c1")
        assert not lim.is_idle("c1")
        time.sleep(1.2)
        assert lim.is_idle("c1")

    def test_stats_shape(self):
        from adam.api.sse_limiter import SSERateLimiter
        lim = SSERateLimiter()
        lim.acquire("c1")
        s = lim.stats()
        assert s["global_active"] == 1
        assert "per_client_active" in s
        assert s["per_client_active"]["c1"] == 1
        lim.release("c1")
        assert lim.stats()["global_active"] == 0


# ── Backup CLI ──────────────────────────────────────────────────────────
class TestBackupCLI:
    def test_backup_help(self):
        env = {**os.environ, "PYTHONPATH": "backend"}
        result = subprocess.run(
            [sys.executable, "-m", "adam.cli.backup", "--help"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parents[2],
            env=env,
        )
        assert "backup" in result.stdout.lower(), result.stdout + result.stderr

    def test_create_and_list_backup(self, tmp_path, monkeypatch):
        # Use the actual workspace root as ADAM_ROOT (so we back up real data)
        # but write to a tmp_path output
        env = {**os.environ, "PYTHONPATH": "backend"}
        out = tmp_path / "backup.tar.gz"
        result = subprocess.run(
            [sys.executable, "-m", "adam.cli.backup", "create", "--output", str(out)],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parents[2],
            env=env,
        )
        assert result.returncode == 0, result.stderr
        assert out.exists()
        result = subprocess.run(
            [sys.executable, "-m", "adam.cli.backup", "list", "--input", str(out)],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parents[2],
            env=env,
        )
        assert "Adam version" in result.stdout, result.stdout

    def test_verify_backup(self, tmp_path):
        env = {**os.environ, "PYTHONPATH": "backend"}
        out = tmp_path / "v.tar.gz"
        result = subprocess.run(
            [sys.executable, "-m", "adam.cli.backup", "create", "--output", str(out)],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parents[2],
            env=env,
        )
        assert result.returncode == 0, result.stderr
        result = subprocess.run(
            [sys.executable, "-m", "adam.cli.backup", "verify", "--input", str(out)],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parents[2],
            env=env,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout
