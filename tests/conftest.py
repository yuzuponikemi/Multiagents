from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage


@pytest.fixture
def mock_llm():
    """LLM mock that returns a fixed AIMessage."""
    llm = MagicMock()
    llm.invoke.return_value = AIMessage(content="mock response")
    return llm


@pytest.fixture
def temp_personas(tmp_path):
    """Create temp persona files for testing."""
    persona_dir = tmp_path / "personas"
    persona_dir.mkdir()
    (persona_dir / "test_agent.md").write_text(
        "# Test Agent\n\n"
        "## Role\n"
        "Test role for unit testing\n\n"
        "## Values\n"
        "- Reliability first\n"
        "- Clean code\n\n"
        "## Biases\n"
        "- Prefers simplicity\n\n"
        "## RACI\n"
        "| Task Area | Level |\n"
        "|-----------|-------|\n"
        "| Testing | R |\n"
        "| Review | C |\n\n"
        "## Background\n"
        "A test agent for validating persona loading.\n"
    )
    return persona_dir


@pytest.fixture
def temp_arc42(tmp_path):
    """Create temp arc42 files for testing."""
    arc42_dir = tmp_path / "arc42"
    arc42_dir.mkdir()
    (arc42_dir / "_section_map.yaml").write_text(
        "test_role:\n"
        "  - 01_intro.md\n"
        "  - 05_blocks.md\n"
        "other_role:\n"
        "  - 01_intro.md\n"
    )
    (arc42_dir / "01_intro.md").write_text("# Introduction\nTest intro content.")
    (arc42_dir / "05_blocks.md").write_text("# Building Blocks\nTest blocks content.")
    return arc42_dir
