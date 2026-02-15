from __future__ import annotations

from multiagents.agent.base import BaseAgent
from multiagents.agent.provider import LLMProvider
from multiagents.config import Settings


def create_ghost(
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
) -> BaseAgent:
    """Create the Architect Ghost agent — C#/design specialist with ADR awareness."""
    return BaseAgent("ghost", settings=settings, provider=provider)
