from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """Shared state passed between agents in a LangGraph workflow."""

    messages: Annotated[list[BaseMessage], add_messages]
    code_base: dict[str, str]  # file path -> content or summary
    jira_context: dict[str, str]  # ticket fields
    review_comments: list[str]
    physical_constraints: dict[str, float]  # instrument-specific limits
    agent_id: str
    current_task: str
    meeting_notes: list[str]
    decision: str
    round_count: int
