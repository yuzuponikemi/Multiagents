from __future__ import annotations

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from multiagents.agent.provider import LLMProvider
from multiagents.agents.analyst import create_analyst
from multiagents.config import Settings
from multiagents.state.graph_state import AgentState
from multiagents.tools.jira_tool import JiraClient, MockJiraClient


def build_triage_graph(
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
    jira_client: JiraClient | None = None,
) -> StateGraph:
    """Build a JIRA ticket triage graph using the Lab Analyst."""
    analyst = create_analyst(settings=settings, provider=provider)
    client = jira_client or MockJiraClient()

    def fetch_ticket_node(state: AgentState) -> AgentState:
        """Fetch ticket from JIRA and add to context."""
        ticket_id = state.get("current_task", "")
        try:
            ticket = client.get_ticket(ticket_id)
            jira_context = {
                "ticket_id": ticket.ticket_id,
                "summary": ticket.summary,
                "description": ticket.description,
                "status": ticket.status,
                "priority": ticket.priority,
                "labels": ", ".join(ticket.labels),
            }
            prompt = (
                f"Triage the following JIRA ticket:\n\n"
                f"**{ticket.ticket_id}: {ticket.summary}**\n"
                f"Priority: {ticket.priority} | Status: {ticket.status}\n"
                f"Labels: {', '.join(ticket.labels)}\n\n"
                f"{ticket.description}\n\n"
                f"Assess the priority, category, affected subsystems, "
                f"and complexity of this issue."
            )
            return {
                **state,
                "jira_context": jira_context,
                "messages": [HumanMessage(content=prompt)],
            }
        except KeyError:
            return {
                **state,
                "jira_context": {"error": f"Ticket {ticket_id} not found"},
                "messages": [
                    HumanMessage(content=f"Ticket {ticket_id} was not found in JIRA.")
                ],
            }

    def analyze_node(state: AgentState) -> AgentState:
        """Run analyst on the ticket."""
        return analyst.invoke(state)

    graph = StateGraph(AgentState)
    graph.add_node("fetch_ticket", fetch_ticket_node)
    graph.add_node("analyze", analyze_node)
    graph.set_entry_point("fetch_ticket")
    graph.add_edge("fetch_ticket", "analyze")
    graph.add_edge("analyze", END)

    return graph


def run_triage(
    ticket_id: str,
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
    jira_client: JiraClient | None = None,
) -> AgentState:
    """Run triage on a JIRA ticket."""
    graph = build_triage_graph(
        settings=settings, provider=provider, jira_client=jira_client
    )
    compiled = graph.compile()

    initial_state: AgentState = {
        "messages": [],
        "code_base": {},
        "jira_context": {},
        "review_comments": [],
        "physical_constraints": {},
        "agent_id": "analyst",
        "current_task": ticket_id,
        "meeting_notes": [],
        "decision": "",
        "round_count": 0,
    }

    return compiled.invoke(initial_state)
