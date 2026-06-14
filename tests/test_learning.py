"""Tests for adam/learning/continuous_learner.py"""

import pytest
from adam.learning.learner import ContinuousLearner

@pytest.fixture
def learner(tmp_path):
    config = {"learning_path": str(tmp_path / "learning")}
    return ContinuousLearner(config)

class TestContinuousLearner:
    """Continuous learner tests"""

    async def test_reflection_short_response(self, learner):
        """Short responses get flagged"""
        result = await learner.reflect("hello", "ok", {"mode": "chat"})
        assert result["feedback"] == "needs_improvement"
        assert "short_response" in result["issues"]

    async def test_reflection_good_response(self, learner):
        """Normal responses pass"""
        result = await learner.reflect(
            "hello",
            "أهلاً بيك! أقدر أساعدك في إيه النهارده؟",
            {"mode": "chat"},
        )
        assert result["feedback"] == "good"

    async def test_reflection_verbose(self, learner):
        """Very long responses flagged"""
        result = await learner.reflect("hello", "x" * 2500, {"mode": "chat"})
        assert result["feedback"] == "needs_improvement"
        assert "verbose" in result["issues"]

    async def test_reflection_uncertainty(self, learner):
        """'مش عارف' triggers uncertainty flag"""
        result = await learner.reflect("question", "أنا مش عارف الإجابة", {"mode": "chat"})
        assert result["feedback"] == "needs_improvement"
        assert "uncertainty" in result["issues"]

    async def test_reflection_persistence(self, learner):
        """Reflections are saved and reloaded"""
        await learner.reflect("test", "good response", {"mode": "chat"})
        assert len(learner._reflections) == 1

        # reload
        learner2 = ContinuousLearner({"learning_path": str(learner.base_path)})
        assert len(learner2._reflections) >= 1

    async def test_extract_knowledge_code(self, learner):
        """Code blocks are extracted as knowledge"""
        result = await learner.extract_knowledge(
            "how to sort?",
            "Use `sorted()`:\n```python\nsorted(list)\n```",
            {"mode": "chat"},
        )
        assert result is not None
        assert result["knowledge_type"] == "code"

    async def test_extract_knowledge_procedure(self, learner):
        """Bold text extracted as procedure knowledge"""
        result = await learner.extract_knowledge(
            "how to do X?",
            "**First** do this\n**Then** do that",
            {"mode": "chat"},
        )
        assert result is not None
        assert result["knowledge_type"] == "procedure"

    async def test_extract_knowledge_plain_only(self, learner):
        """Plain text without code or bold is not extracted"""
        result = await learner.extract_knowledge(
            "how are you?",
            "I'm fine thank you",
            {"mode": "chat"},
        )
        assert result is None

    async def test_generate_skill(self, learner):
        """Knowledge marked as applied generates a skill file"""
        knowledge = {
            "source_message": "How to deploy?",
            "preview": "Use `docker compose up -d`",
            "applied": False,
        }
        name = await learner.generate_skill(knowledge)
        assert name is not None
        assert knowledge["applied"] is True

        skill_path = learner.base_path / "generated_skills" / f"{name}.md"
        assert skill_path.exists()
        content = skill_path.read_text(encoding="utf-8")
        assert "Auto-generated" in content

    async def test_generate_skill_already_applied(self, learner):
        """Already applied knowledge is not regenerated"""
        knowledge = {"applied": True}
        result = await learner.generate_skill(knowledge)
        assert result is None

    async def test_record_feedback(self, learner):
        """Feedback recording and persistence"""
        await learner.record_feedback("message", "response", "good")
        assert len(learner._reinforcement) == 1

        learner2 = ContinuousLearner({"learning_path": str(learner.base_path)})
        assert len(learner2._reinforcement) >= 1

    async def test_process_interaction(self, learner):
        """Full pipeline processes correctly"""
        result = await learner.process_interaction(
            "hello",
            "أهلاً! أنا آدم، عين الحارس.\n```python\nprint('hello')\n```",
            {"mode": "chat"},
        )
        assert result["reflection"] is not None
        assert result["reflection"]["feedback"] == "good"
        assert result["knowledge"] is not None
        assert result["knowledge"]["knowledge_type"] == "code"
        assert result["skill"] is not None

    async def test_get_stats(self, learner):
        """Stats return correct counts"""
        await learner.reflect("m1", "r1", {"mode": "chat"})
        await learner.reflect("m2", "r2", {"mode": "chat"})
        await learner.record_feedback("m1", "r1", "good")

        stats = learner.get_stats()
        assert stats["total_reflections"] == 2
        assert stats["total_feedback"] == 1

    async def test_process_interaction_no_code(self, learner):
        """Plain text interaction skips knowledge/skill"""
        result = await learner.process_interaction(
            "how are you?",
            "Fine thanks",
            {"mode": "chat"},
        )
        assert result["reflection"] is not None
        assert result["knowledge"] is None
        assert result["skill"] is None
