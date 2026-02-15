from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage

from multiagents.config import Settings
from multiagents.graphs.lab_meeting import build_lab_meeting_graph
from multiagents.graphs.triage import build_triage_graph
from multiagents.graphs.unit_review import build_unit_review_graph
from multiagents.state.graph_state import AgentState
from multiagents.tools.jira_tool import MockJiraClient


def _make_test_env(tmp_path):
    """Create test environment with personas and arc42."""
    personas = tmp_path / "personas"
    personas.mkdir()
    for name in ["ghost", "coder", "analyst"]:
        (personas / f"{name}.md").write_text(
            f"# {name.title()}\n\n## Role\nTest {name}\n\n"
            f"## Values\n- V1\n\n## Biases\n- B1\n\n"
            f"## RACI\n| Task Area | Level |\n|---|---|\n| Testing | R |\n"
        )

    arc42 = tmp_path / "arc42"
    arc42.mkdir()
    (arc42 / "_section_map.yaml").write_text(
        "ghost:\n  - 01.md\ncoder:\n  - 01.md\nanalyst:\n  - 01.md\n"
    )
    (arc42 / "01.md").write_text("# Test\nContent.")

    memory = tmp_path / "_memory"
    memory.mkdir()

    settings = Settings(
        project_root=tmp_path,
        personas_dir=personas,
        arc42_dir=arc42,
        memory_dir=memory,
    )
    return settings


def _mock_provider():
    provider = MagicMock()
    provider.name.return_value = "mock:test"
    model = MagicMock()
    model.invoke.return_value = AIMessage(content="APPROVED: Looks good.")
    provider.get_chat_model.return_value = model
    return provider


def _initial_state(**overrides) -> AgentState:
    base: AgentState = {
        "messages": [HumanMessage(content="Test input")],
        "code_base": {},
        "jira_context": {},
        "review_comments": [],
        "physical_constraints": {},
        "agent_id": "test",
        "current_task": "test",
        "meeting_notes": [],
        "decision": "",
        "round_count": 0,
    }
    base.update(overrides)
    return base


class TestUnitReviewGraph:
    def test_build_graph(self, tmp_path):
        settings = _make_test_env(tmp_path)
        provider = _mock_provider()
        graph = build_unit_review_graph(settings=settings, provider=provider)
        compiled = graph.compile()

        result = compiled.invoke(_initial_state())
        assert len(result["messages"]) > 1

    def test_graph_structure(self, tmp_path):
        settings = _make_test_env(tmp_path)
        provider = _mock_provider()
        graph = build_unit_review_graph(settings=settings, provider=provider)
        compiled = graph.compile()
        # Graph should have a review node
        assert "review" in compiled.get_graph().nodes


class TestTriageGraph:
    def test_build_and_run(self, tmp_path):
        settings = _make_test_env(tmp_path)
        provider = _mock_provider()
        client = MockJiraClient()

        graph = build_triage_graph(
            settings=settings, provider=provider, jira_client=client
        )
        compiled = graph.compile()

        state = _initial_state(current_task="CYTO-101", messages=[])
        result = compiled.invoke(state)

        assert result["jira_context"]["ticket_id"] == "CYTO-101"
        assert len(result["messages"]) > 0

    def test_ticket_not_found(self, tmp_path):
        settings = _make_test_env(tmp_path)
        provider = _mock_provider()
        client = MockJiraClient()

        graph = build_triage_graph(
            settings=settings, provider=provider, jira_client=client
        )
        compiled = graph.compile()

        state = _initial_state(current_task="NONEXIST-999", messages=[])
        result = compiled.invoke(state)

        assert "error" in result["jira_context"]


class TestLabMeetingGraph:
    def test_build_and_run_approved(self, tmp_path):
        settings = _make_test_env(tmp_path)
        provider = _mock_provider()  # Returns "APPROVED: Looks good."

        graph = build_lab_meeting_graph(settings=settings, provider=provider)
        compiled = graph.compile()

        state = _initial_state(current_task="test topic")
        result = compiled.invoke(state)

        assert len(result["meeting_notes"]) >= 3  # coder + ghost + analyst
        assert result["round_count"] >= 1

    def test_max_rounds_enforced(self, tmp_path):
        settings = _make_test_env(tmp_path)
        provider = MagicMock()
        provider.name.return_value = "mock:test"
        model = MagicMock()
        # Always return "REVISION NEEDED" to force max rounds
        model.invoke.return_value = AIMessage(content="REVISION NEEDED: Not good enough.")
        provider.get_chat_model.return_value = model

        graph = build_lab_meeting_graph(settings=settings, provider=provider)
        compiled = graph.compile()

        state = _initial_state(current_task="contentious topic")
        result = compiled.invoke(state)

        # Should stop at max rounds (3)
        assert result["round_count"] <= 3

    def test_graph_has_all_nodes(self, tmp_path):
        settings = _make_test_env(tmp_path)
        provider = _mock_provider()
        graph = build_lab_meeting_graph(settings=settings, provider=provider)
        compiled = graph.compile()
        nodes = compiled.get_graph().nodes
        assert "coder" in nodes
        assert "ghost" in nodes
        assert "analyst" in nodes
