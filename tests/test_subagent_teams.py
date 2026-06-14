"""اختبار نظام فرق الوكلاء (subagent teams)"""

import pytest
from adam.subagents.manager import SubagentManager
from adam.subagents.teams import SubagentTeam, TeamManager

class FakeProvider:
    async def chat(self, messages):
        last = messages[-1]["content"] if messages else ""
        return f"Reply to: {last[:50]}"

    @property
    def mode(self):
        return "ollama"

    @property
    def model_name(self):
        return "test-model"

class FakeEngine:
    def __init__(self):
        self.provider = FakeProvider()

class TestSubagentTeam:
    @pytest.mark.asyncio
    async def test_create_team(self):
        team = SubagentTeam(FakeEngine(), name="test-team")
        assert team.name == "test-team"
        assert len(team.agents) == 0

    @pytest.mark.asyncio
    async def test_add_agent(self):
        team = SubagentTeam(FakeEngine())
        team.add_agent("coder", "You write code")
        assert "coder" in team.agents
        assert team.agents["coder"].system_prompt == "You write code"

    @pytest.mark.asyncio
    async def test_add_multiple_agents(self):
        team = SubagentTeam(FakeEngine(), name="dev-team")
        team.add_agent("researcher", "Research")
        team.add_agent("coder", "Code")
        team.add_agent("reviewer", "Review")
        assert len(team.agents) == 3
        assert team._order == ["researcher", "coder", "reviewer"]

    @pytest.mark.asyncio
    async def test_remove_agent(self):
        team = SubagentTeam(FakeEngine())
        team.add_agent("a", "Agent A")
        team.add_agent("b", "Agent B")
        team.remove_agent("a")
        assert "a" not in team.agents
        assert team._order == ["b"]

    @pytest.mark.asyncio
    async def test_run_sequential(self):
        team = SubagentTeam(FakeEngine(), name="seq-team")
        team.add_agent("step1", "You do step 1")
        team.add_agent("step2", "You do step 2")
        result = await team.run("Do the thing", parallel=False)
        assert result["team"] == "seq-team"
        assert result["task"] == "Do the thing"
        assert "step1" in result["results"]
        assert "step2" in result["results"]
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_run_parallel(self):
        team = SubagentTeam(FakeEngine(), name="par-team")
        team.add_agent("a1", "Agent 1")
        team.add_agent("a2", "Agent 2")
        result = await team.run("Task", parallel=True)
        assert result["status"] == "completed"
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_chat_with_agent(self):
        team = SubagentTeam(FakeEngine())
        team.add_agent("helper", "You help")
        result = await team.chat_with_agent("helper", "hello")
        assert "Reply to:" in result.get("response", "")

    @pytest.mark.asyncio
    async def test_chat_with_unknown_agent(self):
        team = SubagentTeam(FakeEngine())
        result = await team.chat_with_agent("ghost", "hi")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_result(self):
        team = SubagentTeam(FakeEngine())
        team.add_agent("w", "Worker")
        await team.run("task", parallel=False)
        result = team.get_agent_result("w")
        assert result is not None
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_get_missing_result(self):
        team = SubagentTeam(FakeEngine())
        assert team.get_agent_result("ghost") is None

    @pytest.mark.asyncio
    async def test_get_status(self):
        team = SubagentTeam(FakeEngine(), name="st-team")
        team.add_agent("a", "Agent A")
        status = team.get_status()
        assert status["name"] == "st-team"
        assert status["agents"] == ["a"]
        assert status["results_count"] == 0

class TestTeamManager:
    @pytest.mark.asyncio
    async def test_create_team(self):
        mgr = TeamManager(FakeEngine())
        team = mgr.create_team("my-team")
        assert team.name == "my-team"
        assert mgr.get_team("my-team") is team

    @pytest.mark.asyncio
    async def test_get_team_not_found(self):
        mgr = TeamManager(FakeEngine())
        assert mgr.get_team("nope") is None

    @pytest.mark.asyncio
    async def test_remove_team(self):
        mgr = TeamManager(FakeEngine())
        mgr.create_team("t1")
        mgr.create_team("t2")
        assert mgr.remove_team("t1") is True
        assert mgr.get_team("t1") is None
        assert len(mgr.list_teams()) == 1

    @pytest.mark.asyncio
    async def test_list_teams(self):
        mgr = TeamManager(FakeEngine())
        mgr.create_team("dev")
        mgr.create_team("ops")
        teams = mgr.list_teams()
        assert len(teams) == 2

    @pytest.mark.asyncio
    async def test_remove_all(self):
        mgr = TeamManager(FakeEngine())
        mgr.create_team("a")
        mgr.create_team("b")
        mgr.remove_all()
        assert len(mgr.list_teams()) == 0

    @pytest.mark.asyncio
    async def test_integration_with_subagent_manager(self):
        mgr = SubagentManager(engine=FakeEngine())
        team = mgr.teams.create_team("integrated-team")
        team.add_agent("w1", "Worker 1")
        team.add_agent("w2", "Worker 2")
        result = await team.run("Integrated task", parallel=True)
        assert result["status"] == "completed"
        assert len(result["results"]) == 2
