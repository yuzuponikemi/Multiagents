from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage

from multiagents.agent.base import BaseAgent
from multiagents.config import Settings


def _make_settings(tmp_path, personas_dir, arc42_dir):
    """Create Settings pointing to temp directories."""
    memory_dir = tmp_path / "_memory"
    memory_dir.mkdir(exist_ok=True)
    return Settings(
        project_root=tmp_path,
        personas_dir=personas_dir,
        arc42_dir=arc42_dir,
        memory_dir=memory_dir,
    )


class TestBaseAgent:
    def test_init_loads_persona(self, tmp_path, temp_personas, temp_arc42):
        settings = _make_settings(tmp_path, temp_personas, temp_arc42)
        mock_provider = MagicMock()
        mock_provider.name.return_value = "mock:test"

        agent = BaseAgent("test_agent", settings=settings, provider=mock_provider)

        assert agent.agent_id == "test_agent"
        assert agent.persona.role == "Test role for unit testing"
        assert "# Role:" in agent.system_prompt

    def test_invoke_calls_llm(self, tmp_path, temp_personas, temp_arc42):
        settings = _make_settings(tmp_path, temp_personas, temp_arc42)
        mock_provider = MagicMock()
        mock_provider.name.return_value = "mock:test"
        mock_model = MagicMock()
        mock_model.invoke.return_value = AIMessage(content="Agent response")
        mock_provider.get_chat_model.return_value = mock_model

        agent = BaseAgent("test_agent", settings=settings, provider=mock_provider)

        state = {
            "messages": [HumanMessage(content="Hello")],
            "code_base": {},
            "jira_context": {},
            "review_comments": [],
            "physical_constraints": {},
            "agent_id": "test_agent",
            "current_task": "test",
        }

        result = agent.invoke(state)

        assert mock_model.invoke.called
        assert len(result["messages"]) == 2
        assert result["messages"][-1].content == "Agent response"

    def test_check_safety(self, tmp_path, temp_personas, temp_arc42):
        settings = _make_settings(tmp_path, temp_personas, temp_arc42)
        mock_provider = MagicMock()
        mock_provider.name.return_value = "mock:test"

        agent = BaseAgent("test_agent", settings=settings, provider=mock_provider)

        safe_result = agent.check_safety("set_laser", {"laser_power_mw": 50})
        assert safe_result.is_safe is True

        unsafe_result = agent.check_safety("disable_interlock", {})
        assert unsafe_result.is_safe is False

    def test_save_and_reload_lesson(self, tmp_path, temp_personas, temp_arc42):
        settings = _make_settings(tmp_path, temp_personas, temp_arc42)
        mock_provider = MagicMock()
        mock_provider.name.return_value = "mock:test"

        agent = BaseAgent("test_agent", settings=settings, provider=mock_provider)

        agent.save_lesson("Always check interlock before laser activation")
        agent.reload_system_prompt()

        assert "interlock" in agent.system_prompt

    def test_repr(self, tmp_path, temp_personas, temp_arc42):
        settings = _make_settings(tmp_path, temp_personas, temp_arc42)
        mock_provider = MagicMock()
        mock_provider.name.return_value = "mock:test"

        agent = BaseAgent("test_agent", settings=settings, provider=mock_provider)
        assert "test_agent" in repr(agent)
        assert "Test role" in repr(agent)

    def test_checkpointer_accessible(self, tmp_path, temp_personas, temp_arc42):
        settings = _make_settings(tmp_path, temp_personas, temp_arc42)
        mock_provider = MagicMock()
        mock_provider.name.return_value = "mock:test"

        agent = BaseAgent("test_agent", settings=settings, provider=mock_provider)
        assert agent.checkpointer is not None
