"""Tests for Adam Memory System — MemorySystem + Qdrant store (SQLite)"""

import os
import json
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from adam.memory.system import MemorySystem
from adam.memory import store as memory_store


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def mem_config():
    return {
        "qdrant_url": "http://localhost:6333",
        "ollama_base": "http://localhost:11434",
        "embedding_model": "nomic-embed-text",
    }


@pytest.fixture
def mem(mem_config):
    return MemorySystem(config=mem_config)


@pytest.fixture
def patch_httpx():
    """Patch _get_client to return a mock AsyncClient"""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.post = AsyncMock()
    mock_client.put = AsyncMock()

    with patch.object(MemorySystem, '_get_client', return_value=mock_client):
        yield mock_client


# ─── MemorySystem Tests ──────────────────────────────────────────────────────

class TestMemoryInit:
    def test_default_config(self):
        m = MemorySystem({"qdrant_url": "http://localhost:6333"})
        assert m.qdrant_url == "http://localhost:6333"
        assert m.ollama_base == "http://localhost:11434"
        assert m.embedding_model == "nomic-embed-text"
        assert m.short_term_limit == 50
        assert m.embed_cache is not None
        assert m.search_cache is not None
        assert len(m.collections) == 6
        assert len(m.short_term) == 0
        assert len(m.episodes) == 0

    def test_override_config(self):
        m = MemorySystem({"qdrant_url": "http://custom:6333", "ollama_base": "http://custom:11434",
                          "embedding_model": "custom-model", "short_term_limit": 10})
        assert m.qdrant_url == "http://custom:6333"
        assert m.ollama_base == "http://custom:11434"
        assert m.embedding_model == "custom-model"
        assert m.short_term_limit == 10


class TestMemoryEmbed:
    @pytest.mark.asyncio
    async def test_embed_caches_result(self, mem, patch_httpx):
        """Test that embed() caches and returns the vector from Ollama"""
        patch_httpx.post.return_value.json = MagicMock(return_value={"embedding": [0.1, 0.2, 0.3]})
        patch_httpx.post.return_value.raise_for_status = MagicMock()

        vec = await mem.embed("test text")
        assert vec == [0.1, 0.2, 0.3]

        # Cache uses TTLCache._key() which hashes the input
        cache_key = mem.embed_cache._key("test text")
        assert mem.embed_cache.get(cache_key) == [0.1, 0.2, 0.3]

        # Second call uses cache, no HTTP request
        patch_httpx.post.reset_mock()
        vec2 = await mem.embed("test text")
        assert vec2 == [0.1, 0.2, 0.3]
        patch_httpx.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_embed_raises_on_failure(self, mem, patch_httpx):
        """embed() doesn't catch HTTP exceptions — they propagate up"""
        patch_httpx.post.side_effect = Exception("Ollama down")
        with pytest.raises(Exception):
            await mem.embed("fail")


class TestMemoryStore:
    @pytest.mark.asyncio
    async def test_store_conversation(self, mem):
        """store_conversation appends to short_term even without Qdrant"""
        mem.embed = AsyncMock(return_value=[0.1] * 768)

        with patch.object(mem, 'store', return_value=True):
            await mem.store_conversation("hello", "world", metadata={"test": True})

        # Verify short_term was updated
        assert len(mem.short_term) > 0
        entry = mem.short_term[-1]
        assert entry["question"] == "hello"
        assert entry["answer"] == "world"
        assert entry["metadata"] == {"test": True}

    @pytest.mark.asyncio
    async def test_store_failure_doesnt_crash(self, mem):
        mem.embed = AsyncMock(return_value=[0.1] * 768)

        with patch.object(mem, 'store', return_value=False):
            await mem.store_conversation("hello", "world")
        # Should not raise even if store fails
        assert len(mem.short_term) > 0

    def test_short_term_max_respected(self, mem):
        for i in range(60):
            mem.short_term.append({"question": f"q{i}", "answer": f"a{i}"})
        assert len(mem.short_term) == 60
        # store_conversation should trim
        mem.embed = AsyncMock(return_value=[0.1] * 768)
        import asyncio
        with patch.object(mem, 'store', return_value=True):
            asyncio.run(mem.store_conversation("trim", "test"))
        assert len(mem.short_term) <= mem.short_term_limit


class TestMemorySearch:
    @pytest.mark.asyncio
    async def test_search_returns_cached_if_available(self, mem):
        cache_key = mem.search_cache._key("test", "knowledge", 5, 0.5)
        mem.search_cache.set(cache_key, [{"id": "cached", "score": 0.9}])
        results = await mem.search("test", collection="knowledge")
        assert results == [{"id": "cached", "score": 0.9}]

    @pytest.mark.asyncio
    async def test_search_returns_empty_without_qdrant(self, mem, patch_httpx):
        mem.embed = AsyncMock(return_value=None)
        results = await mem.search("test", collection="knowledge")
        assert results == []


class TestMemoryRetrieve:
    @pytest.mark.asyncio
    async def test_retrieve_searches_all_collections(self, mem):
        mem.search = AsyncMock(side_effect=lambda q, collection="knowledge", **kw: (
            [{"id": f"{collection}_1", "score": 0.9}]
        ))
        results = await mem.retrieve("test", top_k=5)
        assert len(results) >= 1
        assert mem.search.call_count >= 6  # all collections

    @pytest.mark.asyncio
    async def test_retrieve_raises_on_failure(self, mem):
        """retrieve() lets search() exceptions propagate"""
        mem.search = AsyncMock(side_effect=Exception("Qdrant unavailable"))
        with pytest.raises(Exception):
            await mem.retrieve("test")


class TestMemoryEpisodes:
    def test_add_episode(self, mem):
        mem.add_episode("something happened", {"detail": "test"}, importance=0.8)
        assert len(mem.episodes) == 1
        ep = mem.episodes[0]
        assert ep["event"] == "something happened"
        assert ep["importance"] == 0.8
        assert "timestamp" in ep

    def test_add_episode_default_importance(self, mem):
        mem.add_episode("test event", {})
        assert mem.episodes[0]["importance"] == 0.5


class TestMemoryStats:
    @pytest.mark.asyncio
    async def test_get_stats(self, mem):
        mem.add_episode("e1", {}, 0.5)
        mem.short_term = [{"q": "q1", "a": "a1"}]
        stats = mem.get_stats()
        assert "short_term_count" in stats
        assert "episodic_count" in stats
        assert "collections" in stats
        assert stats["short_term_count"] >= 1
        assert stats["episodic_count"] == 1


# ─── SQLite store (memory_store) Tests ──────────────────────────────────────

class TestMemoryStoreSQLite:
    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Use a temp DB for each test"""
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        old_db = os.environ.get("ADAM_MEMORY_DB")
        os.environ["ADAM_MEMORY_DB"] = self.db_path
        yield
        os.unlink(self.db_path)
        if old_db:
            os.environ["ADAM_MEMORY_DB"] = old_db
        else:
            del os.environ["ADAM_MEMORY_DB"]

    def test_store_and_recall(self):
        mid = memory_store.store("test content", tags="test", priority=3)
        assert isinstance(mid, int)
        assert mid > 0

        recalled = memory_store.recall(mid)
        assert recalled is not None
        assert recalled["content"] == "test content"
        assert recalled["tags"] == "test"
        assert recalled["priority"] == 3

    def test_store_defaults(self):
        mid = memory_store.store("no tags")
        recalled = memory_store.recall(mid)
        assert recalled["tags"] == ""
        assert recalled["priority"] == 3
        assert recalled["source"] == "adam"

    def test_recall_unknown_returns_none(self):
        assert memory_store.recall(999999) is None

    def test_search_finds_content(self):
        memory_store.store("apple banana", tags="fruit")
        memory_store.store("apple pie", tags="dessert")
        memory_store.store("carrot cake", tags="veggie")

        results = memory_store.search("apple", limit=10)
        assert len(results) >= 2

        results = memory_store.search("nonexistent_xyz123", limit=10)
        assert len(results) == 0

    def test_search_orders_by_priority(self):
        mid_low = memory_store.store("low priority item", priority=1)
        mid_high = memory_store.store("high priority item", priority=5)

        results = memory_store.search("priority", limit=10)
        assert len(results) >= 2
        # Highest priority should be first
        assert results[0]["priority"] >= results[-1]["priority"]

    def test_reflect_returns_stats(self):
        memory_store.store("r1", priority=3)
        memory_store.store("r2", priority=1)
        reflection = memory_store.reflect(days=30)
        assert "recent_count" in reflection
        assert "recent" in reflection
        assert "most_accessed" in reflection
        assert "period_days" in reflection
        assert reflection["period_days"] == 30
        assert reflection["recent_count"] >= 2

    def test_stats(self):
        memory_store.store("s1", priority=5)
        memory_store.store("s2", priority=3)
        stats = memory_store.stats()
        assert "total" in stats
        assert "by_priority" in stats
        assert "oldest" in stats
        assert "newest" in stats
        assert "db_path" in stats
        assert stats["total"] >= 2

    def test_priority_clamping(self):
        mid = memory_store.store("high", priority=999)
        rec = memory_store.recall(mid)
        assert rec["priority"] == 5  # clamped to max

        mid2 = memory_store.store("low", priority=-1)
        rec2 = memory_store.recall(mid2)
        assert rec2["priority"] == 1  # clamped to min

    def test_search_updates_access_count(self):
        mid = memory_store.store("access test", priority=3)
        before = memory_store.recall(mid)
        assert before is not None
        count_before = before["access_count"]

        # Search should trigger access count increment
        memory_store.search("access test", limit=10)
        after = memory_store.recall(mid)
        assert after["access_count"] > count_before
