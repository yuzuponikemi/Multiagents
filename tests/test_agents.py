from unittest.mock import MagicMock

from multiagents.agents.analyst import create_analyst
from multiagents.agents.coder import create_coder
from multiagents.agents.ghost import create_ghost
from multiagents.config import Settings


def _make_settings(tmp_path, personas_dir, arc42_dir):
    memory_dir = tmp_path / "_memory"
    memory_dir.mkdir(exist_ok=True)
    return Settings(
        project_root=tmp_path,
        personas_dir=personas_dir,
        arc42_dir=arc42_dir,
        memory_dir=memory_dir,
    )


def _make_personas(tmp_path):
    """Create all three persona files for testing."""
    persona_dir = tmp_path / "personas"
    persona_dir.mkdir(exist_ok=True)

    for name, role in [
        ("ghost", "Senior software architect"),
        ("coder", "Implementation-focused developer"),
        ("analyst", "Laboratory scientist"),
    ]:
        (persona_dir / f"{name}.md").write_text(
            f"# {name.title()}\n\n## Role\n{role}\n\n"
            f"## Values\n- V1\n\n## Biases\n- B1\n\n"
            f"## RACI\n| Task Area | Level |\n|---|---|\n| Testing | R |\n"
        )
    return persona_dir


def _make_arc42(tmp_path):
    arc42_dir = tmp_path / "arc42"
    arc42_dir.mkdir(exist_ok=True)
    (arc42_dir / "_section_map.yaml").write_text(
        "ghost:\n  - 01_intro.md\n"
        "coder:\n  - 01_intro.md\n"
        "analyst:\n  - 01_intro.md\n"
    )
    (arc42_dir / "01_intro.md").write_text("# Introduction\nTest content.")
    return arc42_dir


class TestAgentFactories:
    def test_create_ghost(self, tmp_path):
        personas = _make_personas(tmp_path)
        arc42 = _make_arc42(tmp_path)
        settings = _make_settings(tmp_path, personas, arc42)
        mock_provider = MagicMock()
        mock_provider.name.return_value = "mock:test"

        agent = create_ghost(settings=settings, provider=mock_provider)
        assert agent.agent_id == "ghost"
        assert "architect" in agent.persona.role.lower()

    def test_create_coder(self, tmp_path):
        personas = _make_personas(tmp_path)
        arc42 = _make_arc42(tmp_path)
        settings = _make_settings(tmp_path, personas, arc42)
        mock_provider = MagicMock()
        mock_provider.name.return_value = "mock:test"

        agent = create_coder(settings=settings, provider=mock_provider)
        assert agent.agent_id == "coder"
        assert "developer" in agent.persona.role.lower()

    def test_create_analyst(self, tmp_path):
        personas = _make_personas(tmp_path)
        arc42 = _make_arc42(tmp_path)
        settings = _make_settings(tmp_path, personas, arc42)
        mock_provider = MagicMock()
        mock_provider.name.return_value = "mock:test"

        agent = create_analyst(settings=settings, provider=mock_provider)
        assert agent.agent_id == "analyst"
        assert "scientist" in agent.persona.role.lower()
