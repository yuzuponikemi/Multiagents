from __future__ import annotations

from multiagents.agent.base import BaseAgent
from multiagents.agent.provider import LLMProvider
from multiagents.config import Settings


def create_analyst(
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
) -> BaseAgent:
    """Create the Lab Analyst agent — physical constraints and statistics specialist."""
    return BaseAgent("analyst", settings=settings, provider=provider)
