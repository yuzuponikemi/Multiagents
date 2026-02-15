from __future__ import annotations

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from multiagents.agent.provider import LLMProvider
from multiagents.agents.analyst import create_analyst
from multiagents.agents.coder import create_coder
from multiagents.agents.ghost import create_ghost
from multiagents.config import Settings
from multiagents.state.graph_state import AgentState

MAX_ROUNDS = 3


def build_lab_meeting_graph(
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
) -> StateGraph:
    """
    Build a multi-agent discussion graph (Virtual Meeting).

    Flow:
        Coder (propose) → Ghost (review) → [approved?]
            → Yes: Analyst (physics check) → END
            → No: Coder (revise) → Ghost (re-review) → ... (max 3 rounds)
    """
    coder = create_coder(settings=settings, provider=provider)
    ghost = create_ghost(settings=settings, provider=provider)
    analyst = create_analyst(settings=settings, provider=provider)

    def coder_node(state: AgentState) -> AgentState:
        """Coder proposes or revises a solution."""
        result = coder.invoke(state)
        notes = list(state.get("meeting_notes", []))
        last_msg = result["messages"][-1].content if result["messages"] else ""
        notes.append(f"[Coder] {last_msg[:200]}")
        return {**result, "meeting_notes": notes}

    def ghost_node(state: AgentState) -> AgentState:
        """Ghost reviews the proposal."""
        # Add review instruction
        review_prompt = HumanMessage(
            content=(
                "Review the above proposal. "
                "Check alignment with architecture decisions (ADRs). "
                "Respond with APPROVED if acceptable, or provide specific feedback "
                "for revision. Start your response with 'APPROVED:' or 'REVISION NEEDED:'."
            )
        )
        state_with_prompt = {**state, "messages": list(state["messages"]) + [review_prompt]}
        result = ghost.invoke(state_with_prompt)

        notes = list(state.get("meeting_notes", []))
        last_msg = result["messages"][-1].content if result["messages"] else ""
        notes.append(f"[Ghost] {last_msg[:200]}")

        comments = list(state.get("review_comments", []))
        comments.append(last_msg)

        return {**result, "meeting_notes": notes, "review_comments": comments}

    def analyst_node(state: AgentState) -> AgentState:
        """Analyst checks physical constraints."""
        check_prompt = HumanMessage(
            content=(
                "Review the above discussion for any physical constraint violations. "
                "Check laser power, flow rates, PMT voltages, and pressure values. "
                "Provide your assessment."
            )
        )
        state_with_prompt = {**state, "messages": list(state["messages"]) + [check_prompt]}
        result = analyst.invoke(state_with_prompt)

        notes = list(state.get("meeting_notes", []))
        last_msg = result["messages"][-1].content if result["messages"] else ""
        notes.append(f"[Analyst] {last_msg[:200]}")

        return {
            **result,
            "meeting_notes": notes,
            "decision": "Meeting concluded with physics review.",
        }

    def increment_round(state: AgentState) -> AgentState:
        """Increment round counter for loop control."""
        return {**state, "round_count": state.get("round_count", 0) + 1}

    def should_continue(state: AgentState) -> str:
        """Route based on Ghost's verdict and round count."""
        round_count = state.get("round_count", 0)
        if round_count >= MAX_ROUNDS:
            return "max_rounds"

        comments = state.get("review_comments", [])
        if comments:
            last_review = comments[-1].upper()
            if "APPROVED" in last_review:
                return "approved"

        return "revise"

    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("coder", coder_node)
    graph.add_node("ghost", ghost_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("increment_round", increment_round)

    # Edges
    graph.set_entry_point("coder")
    graph.add_edge("coder", "ghost")
    graph.add_edge("ghost", "increment_round")
    graph.add_conditional_edges(
        "increment_round",
        should_continue,
        {
            "approved": "analyst",
            "revise": "coder",
            "max_rounds": "analyst",
        },
    )
    graph.add_edge("analyst", END)

    return graph


def run_lab_meeting(
    topic: str,
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
) -> AgentState:
    """Run a virtual lab meeting on the given topic."""
    graph = build_lab_meeting_graph(settings=settings, provider=provider)
    compiled = graph.compile()

    initial_state: AgentState = {
        "messages": [
            HumanMessage(
                content=(
                    f"Topic for discussion: {topic}\n\n"
                    f"Please propose a solution or approach for this topic."
                )
            )
        ],
        "code_base": {},
        "jira_context": {},
        "review_comments": [],
        "physical_constraints": {},
        "agent_id": "meeting",
        "current_task": topic,
        "meeting_notes": [],
        "decision": "",
        "round_count": 0,
    }

    return compiled.invoke(initial_state)
