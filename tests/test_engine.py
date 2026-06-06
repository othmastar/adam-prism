"""Basic engine tests - requires Ollama + Qdrant running"""

import pytest
import json
import time
from core.engine import AdamPrismEngine


@pytest.fixture
def config():
    return {
        "ollama_base": "http://localhost:11434",
        "model_name": "gemma4:e4b",
        "qdrant_url": "http://localhost:6333",
        "context_window": 4096,
        "token_budget": 4000,
        "max_conversation_history": 10,
        "max_tool_calls": 2,
        "tool_timeout": 15,
        "cycle_timeout": 60,
    }


@pytest.fixture
async def engine(config):
    eng = AdamPrismEngine(config)
    yield eng


class TestEngineInit:
    def test_defaults(self, engine):
        assert engine.model_name == "gemma4:e4b"
        assert engine.active_mode == "teacher"
        assert engine.cycle_count == 0
        assert len(engine.conversation_history) == 0
        assert engine.max_history == 10

    def test_attach(self, engine):
        mock = {"hello": "world"}
        engine.attach("test_module", mock)
        assert engine.test_module == mock

    def test_quick_classify(self, engine):
        result = engine._quick_classify_intent("ابحث عن الذكاء الاصطناعي")
        assert result["mode"] == "technical_researcher"

        result = engine._quick_classify_intent("اشرح لي الموضوع ده")
        assert result["mode"] == "teacher"

        result = engine._quick_classify_intent("اكتب كود بايثون")
        assert result["mode"] == "software_dev"

    def test_trim_history(self, engine):
        for i in range(20):
            engine.conversation_history.append({"role": "user", "content": f"msg {i}"})
        assert len(engine.conversation_history) == 20
        engine._trim_conversation_history(5)
        assert len(engine.conversation_history) == 5
        assert engine.conversation_history[0]["content"] == "msg 15"

    def test_parse_tool_request(self, engine):
        assert engine._parse_tool_request("Hello") is None

        result = engine._parse_tool_request(
            'Some text\n{"_tool": "browser_open", "params": {"url": "https://x.com"}}'
        )
        assert result is not None
        assert result["_tool"] == "browser_open"
        assert result["params"]["url"] == "https://x.com"


class TestEngineChat:
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_simple_chat(self, engine):
        result = await engine.chat("ما اسمك؟")
        assert "response" in result
        assert len(result["response"]) > 10
        assert result["cycle"] >= 1
        assert result["duration_ms"] > 0
        assert len(engine.conversation_history) == 2

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_url_detection(self, engine):
        result = await engine.chat("افتح https://example.com")
        assert "response" in result
        # Should not contain refusal keywords
        refusal_words = ["لا أملك", "لا أستطيع", "لا يمكن"]
        for word in refusal_words:
            assert word not in result["response"], f"Found refusal: {word}"

    @pytest.mark.asyncio
    async def test_conversation_history_limit(self, engine):
        for i in range(15):
            engine.conversation_history.append({"role": "user", "content": f"msg {i}"})
        engine._trim_conversation_history(10)
        assert len(engine.conversation_history) <= 10

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_multiple_cycles(self, engine):
        r1 = await engine.chat("مرحبا")
        assert r1["cycle"] == 1
        r2 = await engine.chat("كيف حالك؟")
        assert r2["cycle"] == 2
        assert len(engine.conversation_history) == 4


class TestTimeouts:
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_generate_with_timeout(self, engine):
        context = {"intent": {}, "mode": "communicator", "cycle": 1}
        deadline = time.time() + 30
        result = await engine._generate_with_timeout("hello", context, deadline)
        assert len(result) > 0
