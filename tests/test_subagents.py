"""اختبار نظام الوكلاء الفرعيين (subagents)"""

import pytest
from adam.subagents.manager import SubagentManager


class FakeProvider:
    async def chat(self, messages):
        last = messages[-1]["content"] if messages else ""
        return f"Echo: {last}"

    @property
    def mode(self):
        return "ollama"

    @property
    def model_name(self):
        return "test-model"


class FakeEngine:
    def __init__(self):
        self.provider = FakeProvider()


@pytest.mark.asyncio
async def test_spawn():
    mgr = SubagentManager(engine=FakeEngine())
    s = mgr.spawn("agent-1")
    assert s.name == "agent-1"
    assert s.id is not None
    assert len(s.conversation_history) == 0


@pytest.mark.asyncio
async def test_list_sessions():
    mgr = SubagentManager(engine=FakeEngine())
    assert len(mgr.list_sessions()) == 0
    mgr.spawn("a1")
    mgr.spawn("a2")
    assert len(mgr.list_sessions()) == 2


@pytest.mark.asyncio
async def test_get_and_remove():
    mgr = SubagentManager(engine=FakeEngine())
    s = mgr.spawn("temp")
    assert mgr.get(s.id) is s
    assert mgr.remove(s.id) is True
    assert mgr.get(s.id) is None
    assert mgr.remove("nope") is False


@pytest.mark.asyncio
async def test_chat():
    mgr = SubagentManager(engine=FakeEngine())
    s = mgr.spawn("echo")
    result = await s.chat("hello")
    assert "Echo: hello" in result["response"]
    assert result["subagent_name"] == "echo"
    assert len(s.conversation_history) == 2  # user + assistant


@pytest.mark.asyncio
async def test_history_limit():
    mgr = SubagentManager(engine=FakeEngine())
    s = mgr.spawn("limited", config={"max_history": 2})
    for i in range(5):
        await s.chat(f"msg-{i}")
    # max_history=2 → max 4 messages (2 user + 2 assistant)
    assert len(s.conversation_history) <= 4


@pytest.mark.asyncio
async def test_empty_message():
    mgr = SubagentManager(engine=FakeEngine())
    s = mgr.spawn("empty")
    result = await s.chat("")
    assert result["response"] == "..."
    assert len(s.conversation_history) == 0


@pytest.mark.asyncio
async def test_status():
    mgr = SubagentManager(engine=FakeEngine())
    s = mgr.spawn("status-test", config={"system_prompt": "Be concise."})
    status = s.get_status()
    assert status["name"] == "status-test"
    assert status["messages_count"] == 0
    assert "Be concise." in status["system_prompt"]


@pytest.mark.asyncio
async def test_remove_all():
    mgr = SubagentManager(engine=FakeEngine())
    mgr.spawn("a")
    mgr.spawn("b")
    assert len(mgr.list_sessions()) == 2
    mgr.remove_all()
    assert len(mgr.list_sessions()) == 0


@pytest.mark.asyncio
async def test_custom_config():
    mgr = SubagentManager(engine=FakeEngine())
    config = {
        "temperature": 0.9,
        "max_tokens": 2048,
        "system_prompt": "You are a poet.",
        "tools_enabled": True,
    }
    s = mgr.spawn("poet", config=config)
    assert s.temperature == 0.9
    assert s.max_tokens == 2048
    assert s.system_prompt == "You are a poet."
    assert s.tools_enabled is False
