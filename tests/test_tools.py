"""
Tests for the tools package (adam.engine.tools)
"""

import json
import pytest
from unittest.mock import AsyncMock, patch
from typing import Dict

from adam.engine.tools import AdamPrismEngineTools


@pytest.fixture
def tools():
    engine = object.__new__(AdamPrismEngineTools)
    engine.config = {
        "local_bin": "/tmp",
        "data_dir": "/tmp/adam_test",
        "notebook_dir": "/tmp/adam_test/notebook",
        "todo_file": "/tmp/adam_test_todos.json",
        "ollama_base": "http://localhost:11434",
        "qdrant_url": "http://localhost:6333",
    }
    engine.session_id = "test-session"
    engine.permission = type("obj", (), {"pending_request": None})()
    engine.learner = type("obj", (), {"predict": lambda s, t, c: "unknown", "get_summary": lambda s: {}})()
    engine.shared_clients = type("obj", (), {"get": AsyncMock(return_value=AsyncMock())})()
    engine.plugins = None
    engine.security_guard = None
    engine.memory = None
    engine._pw_playwright = None
    engine._pw_browser = None
    engine._pw_page = None
    engine._qdrant_client = None
    return engine


class TestToolsParse:
    def test_parse_tool_request_json(self, tools):
        text = '{"_tool": "shell", "params": {"command": "ls"}}'
        result = tools._parse_tool_request(text)
        assert result == {"_tool": "shell", "params": {"command": "ls"}}

    def test_parse_tool_request_json_in_body(self, tools):
        text = 'Some text then {"_tool": "file_read", "params": {"path": "/tmp/test.txt"}}'
        result = tools._parse_tool_request(text)
        assert result["_tool"] == "file_read"

    def test_parse_tool_request_none(self, tools):
        assert tools._parse_tool_request("just a normal message") is None

    def test_local_bin_property(self, tools):
        assert tools._local_bin == "/tmp"

    def test_data_dir_property(self, tools):
        assert "/tmp/adam_test" in tools._data_dir


class TestToolsShell:
    @pytest.mark.asyncio
    async def test_shell_blocked_command(self, tools):
        result = await tools._tool_shell("shell", {"command": "rm -rf /"})
        assert result["success"] is False
        assert "محظور" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_shell_empty_command(self, tools):
        result = await tools._tool_shell("shell", {"command": ""})
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_shell_unsafe_chars(self, tools):
        result = await tools._tool_shell("shell", {"command": "echo `id`"})
        assert result["success"] is False
        assert "غير آمنة" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_python_exec_blocked_import(self, tools):
        result = await tools._tool_shell("python_exec", {"code": "import os; print('hi')"})
        assert result["success"] is False
        assert "غير آمن" in result.get("error", "")


class TestToolsPlanning:
    @pytest.mark.asyncio
    async def test_planning_list_empty(self, tools):
        result = await tools._tool_planning({"action": "list"})
        assert result["success"] is True
        assert result["action"] == "list"
        assert result["todos"] == []

    @pytest.mark.asyncio
    async def test_planning_create(self, tools):
        with patch("pathlib.Path.exists", return_value=False), \
             patch("pathlib.Path.write_text") as mock_write:
            result = await tools._tool_planning({
                "action": "create", "title": "Test task"
            })
            assert result["success"] is True
            assert result["task"]["title"] == "Test task"

    @pytest.mark.asyncio
    async def test_planning_unknown_action(self, tools):
        result = await tools._tool_planning({"action": "fly"})
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_planning_delete(self, tools):
        todos = json.dumps([{"id": "abc123", "title": "test"}])
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value=todos), \
             patch("pathlib.Path.write_text"):
            result = await tools._tool_planning({"action": "delete", "id": "abc123"})
            assert result["success"] is True
            assert "حذف" in result.get("message", "")

    @pytest.mark.asyncio
    async def test_planning_delete_not_found(self, tools):
        todos = json.dumps([{"id": "abc", "title": "test"}])
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value=todos):
            result = await tools._tool_planning({"action": "delete", "id": "nonexistent"})
            assert result["success"] is False
