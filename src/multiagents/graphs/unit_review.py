from __future__ import annotations

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from multiagents.agent.provider import LLMProvider
from multiagents.agents.ghost import create_ghost
from multiagents.config import Settings
from multiagents.state.graph_state import AgentState


def build_unit_review_graph(
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
) -> StateGraph:
    """Build a single-agent code review graph using the Architect Ghost."""
    ghost = create_ghost(settings=settings, provider=provider)

    def review_node(state: AgentState) -> AgentState:
        return ghost.invoke(state)

    graph = StateGraph(AgentState)
    graph.add_node("review", review_node)
    graph.set_entry_point("review")
    graph.add_edge("review", END)

    return graph


def run_unit_review(
    code: str,
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
) -> AgentState:
    """Run a code review on the given code string."""
    graph = build_unit_review_graph(settings=settings, provider=provider)
    compiled = graph.compile()

    initial_state: AgentState = {
        "messages": [HumanMessage(content=f"Review the following code:\n\n```\n{code}\n```")],
        "code_base": {"input": code},
        "jira_context": {},
        "review_comments": [],
        "physical_constraints": {},
        "agent_id": "ghost",
        "current_task": "code_review",
        "meeting_notes": [],
        "decision": "",
        "round_count": 0,
    }

    return compiled.invoke(initial_state)
