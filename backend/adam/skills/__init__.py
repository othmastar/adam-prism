"""Showcase stub — skill curator is in the full version.

The full version has a closed-loop skill curator that watches
the agent's behavior and creates new skills from successful patterns.

In showcase, this is a no-op so the engine still imports cleanly.
"""
from typing import Any


class SkillCurator:
    """No-op stub for showcase. The full version watches the agent,
    creates new skills from successful patterns, and persists them."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def curate(self, *args: Any, **kwargs: Any) -> None:
        return None

    def register_skill(self, *args: Any, **kwargs: Any) -> str | None:
        return None
