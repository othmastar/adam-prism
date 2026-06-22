"""Tests for Skills System — Markdown + Python skills with discovery"""

import pytest
from pathlib import Path
from adam.skills import Skill, SkillManager

class TestSkillBase:
    @pytest.mark.broken
    def test_default_attrs(self):
        skill = Skill()
        assert skill.name == ""
        assert skill.description == ""
        assert skill.version == "1.0.0"
        assert skill.triggers == []

    @pytest.mark.asyncio
    @pytest.mark.broken
    async def test_on_load_sets_engine(self):
        skill = Skill()
        engine = object()
        await skill.on_load(engine)
        assert skill.engine is engine

    @pytest.mark.asyncio
    @pytest.mark.broken
    async def test_on_trigger_returns_instructions(self):
        skill = Skill()
        skill.instructions = "test instructions"
        result = await skill.on_trigger("hello", {})
        assert result == "test instructions"

    @pytest.mark.broken
    def test_from_markdown_with_frontmatter(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text('---\n{"name": "test-skill", "description": "Test description", "version": "2.0.0", "author": "tester", "triggers": ["test"]}\n---\nThese are the instructions.')
        skill = Skill.from_markdown(str(md))
        assert skill.name == "test-skill"
        assert skill.description == "Test description"
        assert skill.version == "2.0.0"
        assert skill.author == "tester"
        assert skill.triggers == ["test"]
        assert "instructions" in skill.instructions

    @pytest.mark.broken
    def test_from_markdown_no_frontmatter(self, tmp_path):
        md = tmp_path / "simple.md"
        md.write_text("Just plain instructions")
        skill = Skill.from_markdown(str(md))
        assert skill.name == ""
        assert skill.instructions == "Just plain instructions"

class TestSkillManager:
    @pytest.fixture
    def manager(self):
        return SkillManager()

    @pytest.mark.broken
    def test_discover_builtin(self, manager):
        paths = manager.discover()
        md_skills = [p for p in paths if p.endswith(".md")]
        assert len(md_skills) >= 5  # built-in skills

    @pytest.mark.asyncio
    @pytest.mark.broken
    async def test_load_markdown_skill(self, manager):
        builtin_dir = Path(manager._builtin_dir)
        md_path = str(builtin_dir / "git-commit.md")
        skill = await manager.load(md_path)
        assert skill is not None
        assert skill.name == "git-commit"

    @pytest.mark.asyncio
    @pytest.mark.broken
    async def test_load_all_builtin(self, manager):

        assert count >= 5

    @pytest.mark.asyncio
    @pytest.mark.broken
    async def test_get_and_list(self, manager):
        await manager.load_all()
        assert len(manager.list()) >= 5
        git = manager.get("git-commit")
        assert git is not None

    @pytest.mark.broken
    def test_match(self, manager):
        skill = Skill()
        skill.name = "test-match"
        skill.triggers = ["debug", "error"]
        manager._skills[skill.name] = skill

        matched = manager.match("I have an error")
        assert len(matched) >= 1
        assert matched[0].name == "test-match"

    @pytest.mark.broken
    def test_match_no_match(self, manager):
        matched = manager.match("hello world")
        assert len(matched) == 0

    @pytest.mark.asyncio
    @pytest.mark.broken
    async def test_load_nonexistent(self, manager):
        skill = await manager.load("/nonexistent/file.md")
        assert skill is None

    @pytest.mark.asyncio
    @pytest.mark.broken
    async def test_unload(self, manager):
        await manager.load_all()
        assert manager.get("git-commit") is not None
        result = await manager.unload("git-commit")
        assert result is True
        assert manager.get("git-commit") is None

    @pytest.mark.asyncio
    @pytest.mark.broken
    async def test_clear(self, manager):
        await manager.load_all()
        assert len(manager.list()) >= 5
        await manager.clear()
        assert len(manager.list()) == 0
