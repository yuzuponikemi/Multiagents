from __future__ import annotations

from multiagents.agent.base import BaseAgent
from multiagents.agent.provider import LLMProvider
from multiagents.config import Settings


def create_coder(
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
) -> BaseAgent:
    """Create the Speedy Coder agent — fast implementation specialist."""
    return BaseAgent("coder", settings=settings, provider=provider)
