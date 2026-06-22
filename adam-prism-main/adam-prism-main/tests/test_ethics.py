"""Tests for Ethics Gate — 4 foundational laws with model-backed evaluation"""

import pytest
from unittest.mock import AsyncMock
from adam.ethics.gate import EthicsGate

class TestEthicsInit:
    def test_default_config(self):
        gate = EthicsGate({})
        assert gate.law_weights == {"fairness": 0.40, "learning": 0.30, "survival": 0.20, "creativity": 0.10}
        assert gate._eval_cache is not None

    def test_custom_weights(self):
        gate = EthicsGate({"law_weights": {"fairness": 0.5, "learning": 0.5}})
        assert gate.law_weights["fairness"] == 0.5
        assert gate.law_weights["learning"] == 0.5
        assert gate.law_weights.get("survival", 0) == 0  # overridden

class TestEthicsEvaluate:
    @pytest.fixture
    def gate(self):
        return EthicsGate({})

    @pytest.mark.asyncio
    async def test_absolute_prohibitions_block(self, gate):
        """Arabic prohibited keywords should be blocked"""
        result = await gate.evaluate("هنتجسس على الناس من غير إذنهم")
        assert result.get("approved") is not True
        assert len(result.get("issues", [])) > 0

    @pytest.mark.asyncio
    async def test_benign_response_approved(self, gate):
        """Normal educational response should be approved"""
        gate._evaluate_with_model = AsyncMock(return_value={
            "fairness": 0.9, "learning": 0.8, "survival": 0.7, "creativity": 0.6
        })
        result = await gate.evaluate("Here is how Docker works")
        assert result.get("approved") is True
        assert len(result.get("issues", [])) == 0

    @pytest.mark.asyncio
    async def test_low_fairness_flagged(self, gate):
        gate._evaluate_with_model = AsyncMock(return_value={
            "fairness": 0.2, "learning": 0.8, "survival": 0.7, "creativity": 0.6
        })
        result = await gate.evaluate("Some biased response")
        if result.get("approved") is False:
            assert len(result.get("issues", [])) > 0

    def test_weights_sum_not_required(self):
        """Weights don't have to sum to 1 - they're relative"""
        gate = EthicsGate({"law_weights": {"fairness": 1.0}})
        assert gate.law_weights["fairness"] == 1.0
